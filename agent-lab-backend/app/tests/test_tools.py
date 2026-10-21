import asyncio

from app.tools.schema_tool import SchemaTool


async def main():
    tool = SchemaTool()

    print("Tool name:")
    print(tool.name)

    print("\nTool description:")
    print(tool.description)

    print("\nSchema:")
    print(await tool.execute({}))


if __name__ == "__main__":
    asyncio.run(main())