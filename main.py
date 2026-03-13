from dotenv import load_dotenv
load_dotenv()

import uuid
from langchain_core.messages import HumanMessage
from app.graph import build_graph


def main():
    graph = build_graph()
    thread_id = str(uuid.uuid4())

    print("BursarBot (type 'quit' to exit)")
    while True:
        text = input("\nYou: ").strip()
        if text.lower() in {"quit", "exit"}:
            break

        out = out = graph.invoke(
            {"messages": [HumanMessage(content=text)], "entities": {}, "errors": []},
            config={
                "configurable": {"thread_id": thread_id},
                "tags": ["cli", "bursarbot"],
                "metadata": {"user": "sahil", "entrypoint": "main.py"},
                "run_name": "bursarbot_cli_turn",
            },
        )

        print("Bot:", out.get("result"))
        print("Intent:", out.get("intent"))
        if out.get("errors"):
            print("Errors:", out["errors"])


if __name__ == "__main__":
    main()