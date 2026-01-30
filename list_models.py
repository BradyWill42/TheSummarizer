import os

import google.genai as genai


def main() -> None:
    key = os.environ.get("API_KEY_GEMINI")
    print("API_KEY_GEMINI set:", bool(key))
    if not key:
        raise SystemExit("API_KEY_GEMINI not set. Run .\\API_KEY.ps1 first.")

    client = genai.Client(api_key=key)
    models = list(client.models.list())
    print("Total models returned:", len(models))

    def supported_actions(m) -> list[str]:
        return (
            getattr(m, "supported_actions", None)
            or getattr(m, "supported_generation_methods", None)
            or []
        )

    gen_models = [getattr(m, "name", str(m)) for m in models if "generateContent" in supported_actions(m)]
    print("generateContent models:", len(gen_models))
    print("---")
    for name in gen_models:
        print(name)


if __name__ == "__main__":
    main()

