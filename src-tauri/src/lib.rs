#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::{Arc, Mutex};
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Emitter, Manager,
};
use tauri_plugin_shell::{process::CommandChild, ShellExt};

// ── Modules ───────────────────────────────────────────────────────────────────
pub mod schumann;
pub mod memory;

use memory::SidecarClient;

/// Shared handle to the sidecar child process so we can kill it on exit.
type SidecarHandle = Arc<Mutex<Option<CommandChild>>>;

// ── Sidecar status broadcast ──────────────────────────────────────────────────────────────
//
// We emit these events on the main window so the frontend can react:
//   "sidecar:ready"   — backend is up and healthy  → window is shown here
//   "sidecar:error"   — backend failed to start (payload = human-readable reason)

#[derive(Clone, serde::Serialize)]
struct SidecarErrorPayload {
    reason: String,
}

#[derive(Clone, serde::Serialize)]
struct NavigatePayload {
    section: String,
}

// ── IPC bridge types ─────────────────────────────────────────────────────────────────────

/// Payload accepted by the IPC bridge HTTP server.
/// Python POSTs this to http://127.0.0.1:8009/emit
#[derive(serde::Deserialize)]
struct EmitRequest {
    event:   String,
    payload: serde_json::Value,
}

// ── Process-tree kill ─────────────────────────────────────────────────────────────────

#[cfg(target_os = "windows")]
fn kill_process_tree(pid: u32) {
    use std::os::windows::process::CommandExt;
    let _ = std::process::Command::new("taskkill")
        .args(["/F", "/T", "/PID", &pid.to_string()])
        .creation_flags(0x08000000)
        .status();
}

#[cfg(not(target_os = "windows"))]
fn kill_process_tree(pid: u32) {
    unsafe {
        libc::killpg(pid as i32, libc::SIGKILL);
    }
}

fn kill_sidecar(guard: &mut Option<CommandChild>) {
    if let Some(child) = guard.take() {
        let pid = child.pid();
        let _ = child.kill();
        kill_process_tree(pid);
    }
}

// ── IPC bridge server ──────────────────────────────────────────────────────────────────
//
// Listens on 127.0.0.1:8009.  Accepts POST /emit {event, payload} from
// the Python backend and forwards to the Tauri WebView via app_handle.emit().
// Only binds to loopback — not reachable from outside the machine.

fn start_ipc_bridge(app_handle: tauri::AppHandle) {
    use axum::{
        extract::State,
        http::StatusCode,
        routing::post,
        Json, Router,
    };

    let handle = Arc::new(app_handle);

    let router = Router::new()
        .route(
            "/emit",
            post(
                |State(h): State<Arc<tauri::AppHandle>>,
                 Json(req): Json<EmitRequest>| async move {
                    match h.emit(&req.event, &req.payload) {
                        Ok(_)  => (StatusCode::OK, "ok"),
                        Err(e) => {
                            eprintln!("[IPC bridge] emit error: {e}");
                            (StatusCode::INTERNAL_SERVER_ERROR, "emit failed")
                        }
                    }
                },
            ),
        )
        .with_state(handle);

    tauri::async_runtime::spawn(async move {
        let listener = match tokio::net::TcpListener::bind("127.0.0.1:8009").await {
            Ok(l)  => l,
            Err(e) => {
                eprintln!("[IPC bridge] failed to bind :8009 — {e}");
                return;
            }
        };
        println!("[IPC bridge] listening on 127.0.0.1:8009");
        if let Err(e) = axum::serve(listener, router).await {
            eprintln!("[IPC bridge] server error: {e}");
        }
    });
}

// ── Tauri commands ─────────────────────────────────────────────────────────────────────

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from GAIA!", name)
}

#[tauri::command]
fn get_backend_status() -> String {
    "online".to_string()
}

#[tauri::command]
async fn restart_backend(app: tauri::AppHandle) -> Result<String, String> {
    let handle: SidecarHandle = app
        .try_state::<SidecarHandle>()
        .ok_or("sidecar state not initialised")?
        .inner()
        .clone();

    {
        let mut guard = handle.lock().map_err(|e| e.to_string())?;
        kill_sidecar(&mut guard);
    }

    let shell = app.shell();
    let cmd = shell
        .sidecar("gaia-backend")
        .map_err(|e| e.to_string())?;
    let (_rx, child) = cmd.spawn().map_err(|e| e.to_string())?;

    {
        let mut guard = handle.lock().map_err(|e| e.to_string())?;
        *guard = Some(child);
    }

    Ok("restarted".to_string())
}

#[tauri::command]
async fn open_log_dir(app: tauri::AppHandle) -> Result<(), String> {
    use tauri_plugin_opener::OpenerExt;

    let app_data = app
        .path()
        .app_data_dir()
        .map_err(|e| e.to_string())?;
    let logs_dir = app_data.join("logs");

    if !logs_dir.exists() {
        std::fs::create_dir_all(&logs_dir).map_err(|e| e.to_string())?;
    }

    app.opener()
        .open_path(logs_dir.to_string_lossy().to_string(), None::<&str>)
        .map_err(|e| e.to_string())?;

    Ok(())
}

#[tauri::command]
async fn load_ambient_position(app: tauri::AppHandle) -> Result<String, String> {
    let local_data = app
        .path()
        .app_local_data_dir()
        .map_err(|e| e.to_string())?;
    let position_file = local_data.join("ambient-position.json");

    if !position_file.exists() {
        return Ok(String::new());
    }

    std::fs::read_to_string(&position_file).map_err(|e| e.to_string())
}

#[tauri::command]
async fn navigate_main(app: tauri::AppHandle, section: String) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("main") {
        window
            .emit("navigate", NavigatePayload { section })
            .map_err(|e| e.to_string())?;
        let _ = window.show();
        let _ = window.set_focus();
    }
    Ok(())
}

#[tauri::command]
async fn quit_app(app: tauri::AppHandle) {
    if let Some(state) = app.try_state::<SidecarHandle>() {
        if let Ok(mut guard) = state.lock() {
            kill_sidecar(&mut guard);
        }
    }
    app.exit(0);
}

// ── Sidecar startup ────────────────────────────────────────────────────────────────────

fn emit_backend_error(app: &tauri::AppHandle, reason: &str) {
    eprintln!("[GAIA] Backend error: {reason}");

    if let Some(window) = app.get_webview_window("main") {
        let _ = window.emit(
            "sidecar:error",
            SidecarErrorPayload {
                reason: reason.to_string(),
            },
        );
        let _ = window.show();
        let _ = window.set_focus();
    }

    let app_clone = app.clone();
    let reason_owned = reason.to_string();
    tauri::async_runtime::spawn(async move {
        use tauri_plugin_dialog::{DialogExt, MessageDialogKind};
        let _ = app_clone
            .dialog()
            .message(format!(
                "GAIA's Python backend failed to start.\n\n\
                 Reason: {reason_owned}\n\n\
                 Please restart the app. If the problem persists, \
                 check that no other process is using port 52000."
            ))
            .kind(MessageDialogKind::Error)
            .title("GAIA — Backend Error")
            .blocking_show();
    });
}

fn start_python_sidecar(app: &tauri::App, handle: SidecarHandle) {
    let shell = app.shell();
    let app_handle = app.handle().clone();

    let sidecar_result = shell.sidecar("gaia-backend");
    let sidecar_cmd = match sidecar_result {
        Ok(cmd) => cmd,
        Err(e) => {
            emit_backend_error(
                &app_handle,
                &format!("sidecar binary not found — run PyInstaller first ({e})"),
            );
            return;
        }
    };

    tauri::async_runtime::spawn(async move {
        match sidecar_cmd.spawn() {
            Err(e) => {
                emit_backend_error(
                    &app_handle,
                    &format!("failed to launch gaia-backend: {e}"),
                );
            }
            Ok((_rx, child)) => {
                {
                    let mut guard = handle.lock().unwrap();
                    *guard = Some(child);
                }

                let client = reqwest::Client::new();
                let mut delay_ms = 300u64;
                let mut ready = false;

                for attempt in 0..20 {
                    tokio::time::sleep(std::time::Duration::from_millis(delay_ms)).await;
                    match client
                        .get("http://127.0.0.1:52000/health")
                        .timeout(std::time::Duration::from_secs(2))
                        .send()
                        .await
                    {
                        Ok(resp) if resp.status().is_success() => {
                            println!("[GAIA] Python backend ready after attempt {attempt} \u{2713}");
                            ready = true;
                            break;
                        }
                        _ => {}
                    }
                    delay_ms = (delay_ms * 3 / 2).min(3000);
                }

                if ready {
                    let ipc_notify = reqwest::Client::new()
                        .post("http://127.0.0.1:52000/internal/ipc-ready")
                        .timeout(std::time::Duration::from_secs(2))
                        .send()
                        .await;
                    if let Err(e) = ipc_notify {
                        eprintln!("[IPC-ready notify failed (non-fatal): {e}");
                    } else {
                        println!("[GAIA] IPC bridge registered with Python backend \u{2713}");
                    }

                    if let Some(window) = app_handle.get_webview_window("main") {
                        let _ = window.emit("sidecar:ready", ());
                        let _ = window.show();
                        let _ = window.set_focus();
                    }
                } else {
                    emit_backend_error(
                        &app_handle,
                        "health check timed out after 30 s — port 52000 may be blocked",
                    );
                }
            }
        }
    });
}

// ── App entry point ────────────────────────────────────────────────────────────────────

pub fn run() {
    let sidecar_handle: SidecarHandle = Arc::new(Mutex::new(None));

    tauri::Builder::default()
        .manage(sidecar_handle.clone())
        .manage(SidecarClient::new())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
                let _ = window.set_focus();
            }
        }))
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            start_ipc_bridge(app.handle().clone());

            let handle = app.state::<SidecarHandle>().inner().clone();
            start_python_sidecar(app, handle);

            let open = MenuItem::with_id(app, "open", "Open GAIA", true, None::<&str>)?;
            let check_updates =
                MenuItem::with_id(app, "updates", "Check for Updates", true, None::<&str>)?;
            let quit = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&open, &check_updates, &quit])?;

            let _tray = TrayIconBuilder::new()
                .menu(&menu)
                .tooltip("GAIA - Your Sovereign AI")
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "open" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                    "quit" => {
                        if let Some(state) = app.try_state::<SidecarHandle>() {
                            if let Ok(mut guard) = state.lock() {
                                kill_sidecar(&mut guard);
                            }
                        }
                        app.exit(0);
                    }
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        let app = tray.app_handle();
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                })
                .build(app)?;

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                let app = window.app_handle();
                if let Some(state) = app.try_state::<SidecarHandle>() {
                    if let Ok(mut guard) = state.lock() {
                        kill_sidecar(&mut guard);
                    }
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            greet,
            get_backend_status,
            restart_backend,
            open_log_dir,
            load_ambient_position,
            navigate_main,
            quit_app,
            schumann::get_alignment_state,
            // ── Soul Mirror bridge ─────────────────────
            memory::memory_remember,
            memory::memory_recall,
            memory::memory_semantic,
            memory::memory_key_status,
            memory::memory_key_rotate,
            memory::affect_analyze,
            memory::affect_history,
            memory::affect_trend,
            memory::stage_evaluate,
            // ── Onboarding bridge ──────────────────────
            memory::seed_soul_mirror,
        ])
        .run(tauri::generate_context!())
        .expect("error while running GAIA");
}
