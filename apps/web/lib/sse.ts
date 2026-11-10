import type { SseEvent } from "./types";

export function parseSseBuffer(buffer: string): { events: SseEvent[]; rest: string } {
  const parts = buffer.replace(/\r\n/g, "\n").split("\n\n");
  const rest = parts.pop() ?? "";
  const events: SseEvent[] = [];

  for (const part of parts) {
    if (!part.trim()) {
      continue;
    }
    let event = "message";
    const data: string[] = [];
    for (const line of part.split("\n")) {
      if (!line || line.startsWith(":")) {
        continue;
      }
      if (line.startsWith("event:")) {
        event = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        data.push(line.slice(5).replace(/^ /, ""));
      }
    }
    events.push({ event, data: data.join("\n") });
  }

  return { events, rest };
}
