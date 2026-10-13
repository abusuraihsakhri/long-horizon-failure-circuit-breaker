const { test } = require("node:test");
const assert = require("node:assert/strict");
const { evaluate } = require("../web/app.js");

const base = {
  task_id: "TEST-01",
  target_identifier: "KEY-01",
  primary_metric: 10,
  secondary_metric: 4,
  status_descriptor: "NOMINAL",
  is_critical_flag: false
};

test("routine inputs produce no alerts", () => {
  const x = evaluate(base);
  assert.equal(x.overall_urgency, "ROUTINE");
  assert.equal(x.total_alerts, 0);
  assert.equal(x.audit_hash, null);
  assert.equal(x.mode, "local-browser-evaluation");
});

test("primary limit and secondary limit produce warnings", () => {
  const x = evaluate({...base, primary_metric: 25.01, secondary_metric: 12.01});
  assert.equal(x.overall_urgency, "ELEVATED_RISK");
  assert.equal(x.total_alerts, 2);
  assert.equal(x.critical_alerts_count, 0);
});

test("critical flag escalates even with nominal metrics", () => {
  const x = evaluate({...base, is_critical_flag: true});
  assert.equal(x.overall_urgency, "CRITICAL_STAT_PANIC");
  assert.equal(x.critical_alerts_count, 1);
});

test("status descriptors trigger conformance warning", () => {
  const x = evaluate({...base, status_descriptor: "discordant_anomaly"});
  assert.equal(x.total_alerts, 1);
});

test("invalid inputs are rejected", () => {
  assert.throws(() => evaluate({...base, primary_metric: Infinity}), /finite/);
  assert.throws(() => evaluate({...base, primary_metric: 1e12}), /finite/);
  assert.throws(() => evaluate({...base, task_id: " "}), /required/);
  assert.throws(() => evaluate({...base, is_critical_flag: "false"}), /boolean/);
});
