// The pi tests' scripted provider: an OpenAI-compatible endpoint on 127.0.0.1:$FAKE_PORT (fake_server.py), no model.
export default function (pi: any) {
  pi.registerProvider("fake", {
    name: "Fake",
    baseUrl: `http://127.0.0.1:${process.env.FAKE_PORT}/v1`,
    apiKey: "placeholder",
    api: "openai-completions",
    models: [{ type: "chat", id: "fake-chat", name: "Fake chat", reasoning: false, input: ["text"],
               cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }, contextWindow: 100000, maxTokens: 4096 }],
  });
}
