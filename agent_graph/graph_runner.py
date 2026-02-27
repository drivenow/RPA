import argparse
import json
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from agent_graph.nodes import PIPELINE, NodeError
from agent_graph.state import GraphState


def run_pipeline(url: str) -> GraphState:
    state = GraphState(url=url)
    for node in PIPELINE:
        try:
            state = node(state)
        except NodeError as exc:
            state.error_node = exc.node
            state.error_message = exc.message
            break
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description="LangGraph demo pipeline runner")
    parser.add_argument(
        "--source",
        default="https://mp.weixin.qq.com/s/xM9DMeM6lQ1SJX0Kk4tt5g",
        help="文章 URL 或本地 HTML 路径，例如 file:///tmp/demo.html 或 ./test.html",
    )
    parser.add_argument(
        "--dump",
        default="logs/langgraph_runs/latest.json",
        help="将最终状态写入的文件路径",
    )
    args = parser.parse_args()

    state = run_pipeline(args.source)

    dump_path = Path(args.dump)
    dump_path.parent.mkdir(parents=True, exist_ok=True)
    dump_path.write_text(
        json.dumps(state.dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if state.error_node:
        print(f"[ERROR] {state.error_node}: {state.error_message}")
    else:
        print(f"[SUCCESS] summary preview:\n{state.summary[:200]}")
    print(f"详细状态写入: {dump_path}")


if __name__ == "__main__":
    main()
