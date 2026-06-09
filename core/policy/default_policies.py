"""
core/policy/default_policies.py

Default GAIAN permission policy definitions.
Every tool GAIA agents can invoke must have an entry here.
Gaian can override or extend these at runtime via TrustPolicyEngine.

Canon ref: C01 (Gaian sovereignty), SOVEREIGNTY.md
"""

from core.policy.trust_policy_engine import PermissionScope, RiskLevel, ToolPolicy

DEFAULT_TOOL_POLICIES: list[ToolPolicy] = [
    # ---------------------------------------------------------------
    # Memory operations
    # ---------------------------------------------------------------
    ToolPolicy(
        tool_name="read_memory",
        required_scope=PermissionScope.READ_MEMORY,
        risk_level=RiskLevel.LOW,
        description="Read from GAIA session or sovereign memory.",
    ),
    ToolPolicy(
        tool_name="write_memory",
        required_scope=PermissionScope.WRITE_MEMORY,
        risk_level=RiskLevel.MEDIUM,
        description="Write or update entries in sovereign memory.",
    ),
    # ---------------------------------------------------------------
    # Canon operations
    # ---------------------------------------------------------------
    ToolPolicy(
        tool_name="read_canon",
        required_scope=PermissionScope.READ_CANON,
        risk_level=RiskLevel.LOW,
        description="Retrieve Canon passages for RAG grounding.",
    ),
    ToolPolicy(
        tool_name="write_canon",
        required_scope=PermissionScope.WRITE_CANON,
        risk_level=RiskLevel.HIGH,
        requires_explicit_approval=True,
        description="Add or modify Canon entries. Requires Gaian approval.",
    ),
    # ---------------------------------------------------------------
    # File system
    # ---------------------------------------------------------------
    ToolPolicy(
        tool_name="read_file",
        required_scope=PermissionScope.READ_SYSTEM,
        risk_level=RiskLevel.LOW,
        description="Read a local file.",
    ),
    ToolPolicy(
        tool_name="write_file",
        required_scope=PermissionScope.WRITE_FILE,
        risk_level=RiskLevel.HIGH,
        requires_explicit_approval=True,
        description="Write or overwrite a local file. Requires Gaian approval.",
    ),
    ToolPolicy(
        tool_name="delete_file",
        required_scope=PermissionScope.DELETE_FILE,
        risk_level=RiskLevel.CRITICAL,
        requires_explicit_approval=True,
        description="Delete a local file. Always requires Gaian approval.",
    ),
    # ---------------------------------------------------------------
    # LLM inference
    # ---------------------------------------------------------------
    ToolPolicy(
        tool_name="call_llm",
        required_scope=PermissionScope.CALL_LLM,
        risk_level=RiskLevel.LOW,
        pre_approved=True,
        description="Route a prompt to the configured LLM backend.",
    ),
    # ---------------------------------------------------------------
    # External APIs
    # ---------------------------------------------------------------
    ToolPolicy(
        tool_name="call_github",
        required_scope=PermissionScope.CALL_GITHUB,
        risk_level=RiskLevel.MEDIUM,
        description="Call the GitHub API via MCP.",
    ),
    ToolPolicy(
        tool_name="web_search",
        required_scope=PermissionScope.CALL_WEB_SEARCH,
        risk_level=RiskLevel.LOW,
        description="Perform a web search.",
    ),
    ToolPolicy(
        tool_name="call_external_api",
        required_scope=PermissionScope.CALL_EXTERNAL_API,
        risk_level=RiskLevel.HIGH,
        requires_explicit_approval=True,
        description="Generic external API call. Requires Gaian approval.",
    ),
    # ---------------------------------------------------------------
    # Sensitive / biometric
    # ---------------------------------------------------------------
    ToolPolicy(
        tool_name="read_biometrics",
        required_scope=PermissionScope.ACCESS_BIOMETRICS,
        risk_level=RiskLevel.CRITICAL,
        requires_explicit_approval=True,
        description="Access Gaian biometric data (HRV, heart rate, etc.).",
    ),
    ToolPolicy(
        tool_name="read_location",
        required_scope=PermissionScope.ACCESS_LOCATION,
        risk_level=RiskLevel.CRITICAL,
        requires_explicit_approval=True,
        description="Access Gaian location data.",
    ),
    # ---------------------------------------------------------------
    # Code execution
    # ---------------------------------------------------------------
    ToolPolicy(
        tool_name="execute_code",
        required_scope=PermissionScope.EXECUTE_CODE,
        risk_level=RiskLevel.CRITICAL,
        requires_explicit_approval=True,
        description="Execute arbitrary code in the GAIA runtime. Always requires approval.",
    ),
    # ---------------------------------------------------------------
    # Governance
    # ---------------------------------------------------------------
    ToolPolicy(
        tool_name="modify_policy",
        required_scope=PermissionScope.MODIFY_POLICY,
        risk_level=RiskLevel.CRITICAL,
        requires_explicit_approval=True,
        description="Modify the Trust & Permission Policy Engine configuration.",
    ),
    ToolPolicy(
        tool_name="halt_system",
        required_scope=PermissionScope.HALT_SYSTEM,
        risk_level=RiskLevel.CRITICAL,
        requires_explicit_approval=True,
        description="Halt all GAIA sessions. Requires Gaian approval.",
    ),
]
