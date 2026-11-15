/* Backend packet checks shared by the simulator and external packet sources. */
class PacketClient {
  constructor({ apiBase = "", streamId, fetchImpl = globalThis.fetch.bind(globalThis), timeoutMs = 5000 }) {
    this.endpoint = `${apiBase.replace(/\/+$/, "")}/api/packet-streams/${encodeURIComponent(streamId)}/packets`;
    this.streamId = streamId;
    this.fetchImpl = fetchImpl;
    this.timeoutMs = timeoutMs;
    this.delivered = new Set();
  }

  async check(packet) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      const response = await this.fetchImpl(this.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(packet),
        signal: controller.signal,
      });
      if (response.status === 409 || response.status === 422) return { status: "rejected" };
      if (response.status !== 200 && response.status !== 201) {
        throw new Error(`Packet API returned ${response.status}`);
      }
      const receipt = await response.json();
      if (receipt.stream_id !== this.streamId || receipt.seq !== packet.seq
          || !Number.isInteger(receipt.id) || receipt.id < 1 || typeof receipt.duplicate !== "boolean") {
        throw new Error("Packet API returned an invalid receipt");
      }
      if (this.delivered.has(packet.seq)) return { status: "duplicate" };
      this.delivered.add(packet.seq);
      // A retry can return duplicate=true after the server committed but its
      // response was lost. Deliver it once if this page has not plotted it yet.
      return { status: "accepted" };
    } catch (error) {
      return {
        status: "unavailable",
        message: error.name === "AbortError" ? "Packet API timed out" : "Packet API unavailable",
      };
    } finally {
      clearTimeout(timeout);
    }
  }
}

if (typeof module !== "undefined" && module.exports) module.exports = { PacketClient };
