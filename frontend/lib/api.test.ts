import { describe, expect, it } from "vitest";

import { ApiRequestError, exportUrl, API_URL } from "./api";

describe("api layer", () => {
  it("builds export urls with format", () => {
    expect(exportUrl("abc123", "reviews_csv")).toBe(`${API_URL}/api/export/abc123?format=reviews_csv`);
  });

  it("exposes structured errors", () => {
    const err = new ApiRequestError("INVALID_CSV", "bad file", 400, { a: 1 });
    expect(err.code).toBe("INVALID_CSV");
    expect(err.status).toBe(400);
    expect(err.details).toEqual({ a: 1 });
    expect(err.message).toBe("bad file");
  });

  it("uses the env-provided API url", () => {
    expect(API_URL).toBe(process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000");
  });
});
