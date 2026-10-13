"use strict";

/*
 * Browser-only deterministic evaluation. This does not run the Python API,
 * persist audit records, or generate a cryptographic HMAC.
 */
function evaluate(input) {
  const taskId = String(input.task_id ?? "").trim();
  const targetId = String(input.target_identifier ?? "").trim();
  const descriptor = String(input.status_descriptor ?? "").trim();
  const primary = Number(input.primary_metric);
  const secondary = Number(input.secondary_metric);
  if (!taskId || !targetId || !descriptor) {
    throw new Error("Task ID, target identifier and status descriptor are required.");
  }
  if (![primary, secondary].every(Number.isFinite) ||
      [primary, secondary].some(v => Math.abs(v) > 1e9)) {
    throw new Error("Metrics must be finite numbers between -1,000,000,000 and 1,000,000,000.");
  }
  if (typeof input.is_critical_flag !== "boolean") {
    throw new Error("Critical flag must be a boolean.");
  }

  const alerts = [];
  function alert(worker, urgency, summary, details, remediation) {
    alerts.push({
      origin_worker: worker, urgency, summary,
      technical_details: details, actionable_remediation: remediation
    });
  }
  if (primary > 25) {
    alert("InvariantQCWorker", "ELEVATED_RISK", "Primary Metric Threshold Exceeded",
      "Primary measurement " + primary.toFixed(2) + " exceeds threshold 25.00.",
      "Review the primary parameter.");
  }
  if (input.is_critical_flag || secondary > 12) {
    alert("SafetyEscalationWorker",
      input.is_critical_flag ? "CRITICAL_STAT_PANIC" : "ELEVATED_RISK",
      "Safety Interlock Triggered",
      "CriticalFlag=" + input.is_critical_flag + ", secondary index=" + secondary.toFixed(2),
      "Review escalation criteria.");
  }
  if (["DISCORDANT", "ANOMALY", "MUTANT", "VIOLATION", "FAIL", "REJECT"]
      .some(term => descriptor.toUpperCase().includes(term))) {
    alert("ProtocolConformanceWorker", "ELEVATED_RISK",
      "Protocol Conformance Discordance Detected",
      "Descriptor: " + descriptor, "Review the status descriptor.");
  }
  const critical = alerts.filter(a => a.urgency === "CRITICAL_STAT_PANIC").length;
  const elevated = alerts.filter(a => a.urgency === "ELEVATED_RISK").length;
  const urgency = critical ? "CRITICAL_STAT_PANIC" : elevated ? "ELEVATED_RISK" : "ROUTINE";
  return {
    mode: "local-browser-evaluation",
    task_id: taskId,
    target_identifier: targetId,
    overall_urgency: urgency,
    integrity_status: critical ? "RECALIBRATION_REQUIRED" :
      elevated ? "DISCORDANT_ANOMALY" : "VALIDATED_OPTIMAL",
    total_alerts: alerts.length,
    critical_alerts_count: critical,
    alerts,
    audit_hash: null,
    note: "Local deterministic evaluation only; no signed audit trail or remote processing."
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { evaluate };
}

if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("audit-form");
    const output = document.getElementById("output");
    const status = document.getElementById("status");
    const count = document.getElementById("count");
    const exportButton = document.getElementById("export");
    let result = null, evaluated = 0;

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      try {
        const fields = new FormData(form);
        // Number("") is 0, so explicitly reject blank numeric fields.
        for (const key of ["primary_metric", "secondary_metric"]) {
          if (!String(fields.get(key) ?? "").trim()) {
            throw new Error("Both numeric metrics are required.");
          }
        }
        result = evaluate({
          task_id: fields.get("task_id"),
          target_identifier: fields.get("target_identifier"),
          primary_metric: fields.get("primary_metric"),
          secondary_metric: fields.get("secondary_metric"),
          status_descriptor: fields.get("status_descriptor"),
          is_critical_flag: fields.has("is_critical_flag")
        });
        evaluated++;
        count.textContent = String(evaluated);
        status.textContent = result.overall_urgency;
        output.textContent = JSON.stringify(result, null, 2);
        exportButton.disabled = false;
      } catch (error) {
        result = null;
        exportButton.disabled = true;
        status.textContent = "INPUT ERROR";
        output.textContent = error.message;
      }
    });

    exportButton.addEventListener("click", function () {
      if (!result) return;
      const blob = new Blob([JSON.stringify(result, null, 2) + "\n"],
        {type: "application/json"});
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "circuit-breaker-evaluation.json";
      link.click();
      setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    });
  });
}
