import { describe, expect, it } from "vitest";

import { parseSseBuffer } from "./sse";

describe("parseSseBuffer", () => {
  it("parses a complete event and keeps a partial frame", () => {
    const buffer = 'event: step\ndata: {"node":"planner"}\n\nevent: report\ndata: {"ok":';
    const parsed = parseSseBuffer(buffer);
    expect(parsed.events).toEqual([{ event: "step", data: '{"node":"planner"}' }]);
    expect(parsed.rest).toBe('event: report\ndata: {"ok":');
  });

  it("joins a split frame on the next chunk", () => {
    const first = parseSseBuffer('event: done\ndata: {"status":');
    const parsed = parseSseBuffer(`${first.rest}true}\n\n`);
    expect(parsed.events).toEqual([{ event: "done", data: '{"status":true}' }]);
    expect(parsed.rest).toBe("");
  });

  it("reads two events from one chunk", () => {
    const parsed = parseSseBuffer("event: step\ndata: one\n\nevent: report\ndata: two\n\n");
    expect(parsed.events.map((event) => event.event)).toEqual(["step", "report"]);
    expect(parsed.events.map((event) => event.data)).toEqual(["one", "two"]);
  });
});
