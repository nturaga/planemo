"""Module describing the planemo ``bioc_tool_init`` command."""
import os
import sys

import click

from planemo import bioc_tool_builder
from planemo import bioconductor_skeleton
from planemo import io
from planemo import options
from planemo.cli import command_function
from planemo.io import info


REUSING_MACROS_MESSAGE = ("Macros file macros.xml already exists, assuming "
                          " it has relevant planemo-generated definitions.")


# --input_format
# --output_format
# --advanced_options
@click.option(
    "-i",
    "--id",
    type=click.STRING,
    prompt=True,
    help="Short identifier for new tool (no whitespace)",
)
@options.force_option(what="tool")
@click.option(
    "-t",
    "--tool",
    default=None,
    type=click.Path(exists=False,
                    file_okay=True,
                    dir_okay=False,
                    writable=True,
                    resolve_path=True),
    help="Output path for new tool (default is <id>.xml)",
)
@click.option(
    "-n",
    "--name",
    type=click.STRING,
    prompt=True,
    help="Name for new Bioconductor tool (user facing)",
)
@click.option(
    "--version",
    default="0.1.0",
    type=click.STRING,
    help="Tool XML version.",
)
@click.option(
    "-d",
    "--description",
    type=click.STRING,
    default=None,
    prompt=False,
    help="Short description for new tool (user facing)",
)
@click.option(
    "-c",
    "--command",
    type=click.STRING,
    default=None,
    prompt=False,
    help=("Command potentially including cheetah variables"
          "(e.g. 'seqtk seq -a $input > $output')"),
)
@click.option(
    "--help_from_command",
    type=click.STRING,
    default=None,
    prompt=False,
    help="Auto populate help from supplied command.",
)
@click.option(
    "--example_command",
    type=click.STRING,
    default=None,
    prompt=False,
    help=("Example to command with paths to build Cheetah template from "
          "(e.g. 'seqtk seq -a 2.fastq > 2.fasta'). Option cannot be used "
          "with --command, should be used --example_input and "
          "--example_output."),
)
@click.option(
    "--example_input",
    type=click.STRING,
    default=None,
    prompt=False,
    multiple=True,
    help=("For use with --example_command, replace input file (e.g. 2.fastq "
          "with a data input parameter)."),
)
@click.option(
    "--example_output",
    type=click.STRING,
    default=None,
    prompt=False,
    multiple=True,
    help=("For use with --example_command, replace input file (e.g. 2.fastq "
          "with a tool output)."),
)
@click.option(
    "--input",
    type=click.STRING,
    default=None,
    prompt=False,
    multiple=True,
    help="An input description (e.g. input.fasta)",
)
@click.option(
    "--output",
    type=click.STRING,
    multiple=True,
    default=None,
    prompt=False,
    help=("An output location (e.g. output.bam), the Galaxy datatype is "
          "inferred from the extension."),
)
@click.option(
    "--help_text",
    type=click.STRING,
    default=None,
    prompt=False,
    help="Help text (reStructuredText)",
)
@click.option(
    "--doi",
    type=click.STRING,
    default=None,
    multiple=True,
    prompt=False,
    help=("Supply a DOI (http://www.doi.org/) easing citation of the tool "
          "for Galxy users (e.g. 10.1101/014043).")
)
@click.option(
    "--requirement",
    type=click.STRING,
    default=None,
    multiple=True,
    prompt=True,
    help=("Give the name of the bioconductor package,"
          "requirements will be set using bioconda. eg: 'motifbreakR' ")
)
@click.option(
    "--named_output",
    type=click.STRING,
    multiple=True,
    default=None,
    prompt=False,
    help=("Create a named output for use with command block for example "
          "specify --named_output=output1.bam and then use '-o $ouput1' "
          "in your command block."),
)
@click.option(
    "--test_case",
    is_flag=True,
    default=None,
    prompt=False,
    help=("For use with --example_commmand, generate a tool test case from "
          "the supplied example."),
)
@click.option(
    "--macros",
    is_flag=True,
    default=None,
    prompt=False,
    help="Generate a macros.xml for reuse across many tools.",
)
@click.option(
    "--cite_url",
    type=click.STRING,
    default=None,
    multiple=True,
    prompt=False,
    help=("Supply a URL for citation.")
)
@click.option(
    "--bioconda_path",
    type=click.STRING,
    default=None,
    prompt=True,
    help=("Give path to bioconda repository,"
          " if left empty, path will be made in home directory")
)
@click.command("bioc_tool_init")
@command_function
def cli(ctx, **kwds):
    """Generate a bioconductor tool outline from supplied arguments.
    """
    # info("arguments: \n")
    # for count, thing in enumerate(kwds):
    #     info("{0}.{1}".format(count, thing))

    invalid = _validate_kwds(kwds)

    # info("invalid arguments: \n", invalid)

    if invalid:
        return invalid
    output = kwds.get("tool")
    if not output:
        output = "%s.xml" % kwds.get("id")
    if not io.can_write_to_path(output, **kwds):
        sys.exit(1)
    info("Tool building starts here")
    tool_description = bioc_tool_builder.build(**kwds)
    info("Tool definition file: \n")
    print(type(tool_description))
    open(output, "w").write(tool_description.contents)
    io.info("Tool written to %s" % output)
    macros = kwds["macros"]
    macros_file = "macros.xmll"
    if macros and not os.path.exists(macros_file):
        open(macros_file, "w").write(tool_description.macro_contents)
    elif macros:
        io.info(REUSING_MACROS_MESSAGE)
    if tool_description.test_files:
        if not os.path.exists("test-data"):
            io.info("No test-data directory, creating one.")
            io.shell("mkdir -p 'test-data'")
        for test_file in tool_description.test_files:
            io.info("Copying test-file %s" % test_file)
            io.shell("cp '%s' 'test-data'" % test_file)


def _validate_kwds(kwds):
    def not_exclusive(x, y):
        if kwds.get(x) and kwds.get(y):
            io.error("Can only specify one of --%s and --%s" % (x, y))
            return True

    def not_specifing_dependent_option(x, y):
        if kwds.get(x) and not kwds.get(y):
            template = "Can only use the --%s option if also specifying --%s"
            message = template % (x, y)
            io.error(message)
            return True

    if not_exclusive("help_text", "help_from_command"):
        return 1
    if not_exclusive("command", "example_command"):
        return 1
    if not_specifing_dependent_option("example_input", "example_command"):
        return 1
    if not_specifing_dependent_option("example_output", "example_command"):
        return 1
    if not_specifing_dependent_option("test_case", "example_command"):
        return 1
    return 0
