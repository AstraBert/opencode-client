import os

from dataclasses import dataclass, field
from typing import TypedDict, Literal
from typing_extensions import NotRequired


class ToolArgSpecs(TypedDict):
    """
    NOTE: this API is in beta. Expect changes.

    Describe a tool argument.

    Attributes:
        type (Literal["string", "number", "boolean"]): type of the argument
        description (NotRequired[str]): description of the argument
    """

    type: Literal[
        "string", "number", "boolean"
    ]  # support only for these basic type in beta
    description: NotRequired[str]


@dataclass
class CustomTool:
    """
    NOTE: this API is in beta. Expect changes.

    Define a custom tool with

    Attributes:
        name (str): name of the tool
        description (str): description of the tool
        fn (str): function definition (define the tool function with TypeScript)
        args: tool arguments as a dictionary with the name of the argument as key and the type and (optional) description as a value.
    """

    name: str
    description: str
    fn: str
    args: dict[str, ToolArgSpecs] = field(default_factory=dict)

    def to_file(self) -> None:
        file_name = self.name.lower().replace(" ", "_") + ".ts"
        if not os.path.exists(".opencode/tool/"):
            os.makedirs(".opencode/tool/", exist_ok=True)
        if os.path.exists(".opencode/tool/" + file_name):
            raise ValueError(
                f"Please provide a different name (file {file_name}) already exists in `.opencode/tool`"
            )
        with open(".opencode/tool/" + file_name, "w") as f:
            f.write("import { tool } from '@opencode-ai/plugin'\n\n")
            f.write("export default tool({\n")
            f.write(f'\tdescription: "{self.description}",\n')
            f.write("\targs: {\n")
            for arg, argspecs in self.args.items():
                if argspecs.get("description"):
                    f.write(
                        f"\t\t{arg}: tool.schema.{argspecs.get('type')}().describe('{argspecs.get('description')}')\n"
                    )
                else:
                    f.write(f"\t\t{arg}: tool.schema.{argspecs.get('type')}()\n")
            f.write("\t},\n")
            f.write("\tasync execute(args) {\n")
            f.write(f"\t\t{self.fn}\n")
            f.write("\t},\n")
            f.write("})")
        return None
