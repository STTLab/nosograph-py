from __future__ import annotations
import gzip


def _open_vcf(vcf_path: str):
    """Open a VCF for text reading, transparently handling gzip (.gz)."""
    if vcf_path.endswith(".gz"):
        return gzip.open(vcf_path, "rt", encoding="utf-8")
    return open(vcf_path, encoding="utf-8")


def _to_int(val: str | None) -> int | None:
    if val is None or val == ".":
        return None
    try:
        return int(val)
    except ValueError:
        return None


def _parse_ann(ann_str: str) -> list[dict]:
    """Parse a SnpEff ANN INFO field into one dict per annotation entry.

    ANN format (pipe-delimited per entry, comma-separated entries):
      ALLELE|EFFECT|IMPACT|GENE_NAME|GENE_ID|FEATURE_TYPE|TRANSCRIPT_ID|
      BIOTYPE|RANK|HGVS.c|HGVS.p|cDNA.pos|CDS.pos|AA.pos|DISTANCE|ERRORS
    """
    results = []
    for entry in ann_str.split(","):
        fields = entry.split("|")
        if len(fields) < 11:
            continue
        results.append({
            "effect": fields[1],
            "impact": fields[2],
            "gene_name": fields[3] or None,
            "hgvs_c": fields[9],
            "hgvs_p": fields[10],
        })
    return results


def _parse_info(info_str: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for token in info_str.split(";"):
        if "=" in token:
            k, v = token.split("=", 1)
            result[k] = v
        else:
            result[token] = "true"
    return result


def _parse_format(format_str: str, sample_str: str) -> dict[str, str]:
    keys = format_str.split(":")
    values = sample_str.split(":")
    return dict(zip(keys, values))


def parse_medaka_vcf(vcf_path: str, ref_accession: str, sample_id: str) -> list[dict]:
    """Parse a Medaka+SnpEff annotated VCF (VCFv4.1).

    One output dict is emitted per (VCF row × ANN annotation). Each dict
    contains all fields needed for the BULK_MERGE_Variants Cypher query.
    FORMAT is expected to contain at least GT and GQ.
    """
    records: list[dict] = []
    with _open_vcf(vcf_path) as fh:
        for line in fh:
            if line.startswith("##"):
                continue
            if line.startswith("#CHROM"):
                continue
            cols = line.rstrip("\n").split("\t")
            if len(cols) < 8:
                continue
            chrom, pos_str, _, ref, alt, qual_str, flt, info_str = cols[:8]
            format_str = cols[8] if len(cols) > 8 else ""
            sample_str = cols[9] if len(cols) > 9 else ""

            info = _parse_info(info_str)
            fmt = _parse_format(format_str, sample_str) if format_str else {}
            ann_str = info.get("ANN", "")
            annotations = _parse_ann(ann_str)

            base = {
                "REF_ACC": ref_accession,
                "CHROM": chrom,
                "POS": int(pos_str),
                "REF": ref,
                "ALT": alt,
                "TYPE": info.get("TYPE"),
                "sample_id": sample_id,
                "DP": _to_int(info.get("DP")),
                "GT": fmt.get("GT"),
                "QUAL": float(qual_str) if qual_str not in (".", "") else None,
                "GQ": _to_int(fmt.get("GQ")),
                "AO": None,
                "RO": None,
                "FILTER": flt if flt != "." else None,
                "vcf_source": "medaka",
            }

            if not annotations:
                records.append({**base, "hgvs_c": "", "hgvs_p": "", "EFFECT": None, "IMPACT": None, "gene_name": None})
                continue

            for ann in annotations:
                records.append({
                    **base,
                    "hgvs_c": ann["hgvs_c"],
                    "hgvs_p": ann["hgvs_p"],
                    "EFFECT": ann["effect"],
                    "IMPACT": ann["impact"],
                    "gene_name": ann["gene_name"],
                })
    return records


def parse_snippy_vcf(vcf_path: str, ref_accession: str, sample_id: str) -> list[dict]:
    """Parse a Snippy/freebayes+SnpEff annotated VCF (VCFv4.2).

    One output dict is emitted per (VCF row × ANN annotation). Each dict
    contains all fields needed for the BULK_MERGE_Variants Cypher query.
    FORMAT is expected to contain GT, DP, RO, QR, AO, QA, GL.
    """
    records: list[dict] = []
    with _open_vcf(vcf_path) as fh:
        for line in fh:
            if line.startswith("##"):
                continue
            if line.startswith("#CHROM"):
                continue
            cols = line.rstrip("\n").split("\t")
            if len(cols) < 8:
                continue
            chrom, pos_str, _, ref, alt, qual_str, flt, info_str = cols[:8]
            format_str = cols[8] if len(cols) > 8 else ""
            sample_str = cols[9] if len(cols) > 9 else ""

            info = _parse_info(info_str)
            fmt = _parse_format(format_str, sample_str) if format_str else {}
            ann_str = info.get("ANN", "")
            annotations = _parse_ann(ann_str)

            dp_raw = fmt.get("DP") or info.get("DP")
            ao_raw = fmt.get("AO") or info.get("AO")
            ro_raw = fmt.get("RO") or info.get("RO")

            base = {
                "REF_ACC": ref_accession,
                "CHROM": chrom,
                "POS": int(pos_str),
                "REF": ref,
                "ALT": alt,
                "TYPE": info.get("TYPE"),
                "sample_id": sample_id,
                "DP": _to_int(dp_raw),
                "GT": fmt.get("GT"),
                "QUAL": float(qual_str) if qual_str not in (".", "") else None,
                "GQ": None,
                "AO": _to_int(ao_raw),
                "RO": _to_int(ro_raw),
                "FILTER": flt if flt != "." else None,
                "vcf_source": "snippy",
            }

            if not annotations:
                records.append({**base, "hgvs_c": "", "hgvs_p": "", "EFFECT": None, "IMPACT": None, "gene_name": None})
                continue

            for ann in annotations:
                records.append({
                    **base,
                    "hgvs_c": ann["hgvs_c"],
                    "hgvs_p": ann["hgvs_p"],
                    "EFFECT": ann["effect"],
                    "IMPACT": ann["impact"],
                    "gene_name": ann["gene_name"],
                })
    return records
