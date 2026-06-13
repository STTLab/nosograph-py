import os
import pytest
from nosograph.pipeline import NosoGraphPipelineOutput


CANU_FILES = {
    "assembly.contigs.fasta",
    "assembly.unitigs.fasta",
    "assembly.unassembled.fasta",
    "assembly.report",
}

FLYE_FILES = {
    "assembly.contigs.fasta",
    "assembly_graph.gfa",
    "assembly_graph.gv",
    "assembly_info.txt",
    "flye.log",
    "params.json",
}


def _make_assembly_files(outdir, filenames):
    asm_dir = os.path.join(str(outdir), NosoGraphPipelineOutput.ASSEMBLY_OUTPUT_DIR)
    os.makedirs(asm_dir, exist_ok=True)
    for name in filenames:
        with open(os.path.join(asm_dir, name), "w", encoding="utf-8") as fh:
            fh.write("")


class TestCheckOutputDirectory:
    def test_both_dirs_present(self, tmp_path):
        for d in (
            NosoGraphPipelineOutput.ASSEMBLY_OUTPUT_DIR,
            NosoGraphPipelineOutput.POLISH_OUTPUT_DIR,
        ):
            (tmp_path / d).mkdir()
        out = NosoGraphPipelineOutput("flye", tmp_path)
        assert out.check_output_directory() is True

    def test_missing_polish_dir(self, tmp_path):
        (tmp_path / NosoGraphPipelineOutput.ASSEMBLY_OUTPUT_DIR).mkdir()
        out = NosoGraphPipelineOutput("flye", tmp_path)
        assert out.check_output_directory() is False


class TestCheckOutputFilesCanu:
    def test_all_present(self, tmp_path):
        _make_assembly_files(tmp_path, CANU_FILES)
        out = NosoGraphPipelineOutput("canu", tmp_path)
        assert out.check_output_files() is True

    def test_missing_one_file(self, tmp_path):
        _make_assembly_files(tmp_path, CANU_FILES - {"assembly.report"})
        out = NosoGraphPipelineOutput("canu", tmp_path)
        assert out.check_output_files() is False

    def test_no_longer_raises_not_implemented(self, tmp_path):
        # Regression: canu used to raise NotImplementedError.
        out = NosoGraphPipelineOutput("canu", tmp_path)
        assert out.check_output_files() is False  # empty dir → files absent, no exception


class TestCheckOutputFilesFlye:
    def test_all_present(self, tmp_path):
        _make_assembly_files(tmp_path, FLYE_FILES)
        out = NosoGraphPipelineOutput("flye", tmp_path)
        assert out.check_output_files() is True

    def test_missing_one_file(self, tmp_path):
        _make_assembly_files(tmp_path, FLYE_FILES - {"flye.log"})
        out = NosoGraphPipelineOutput("flye", tmp_path)
        assert out.check_output_files() is False
