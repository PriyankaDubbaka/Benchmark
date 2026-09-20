// Generated from actual pilot artifacts; not mock results.
export const data:any = {
  "metrics": {
    "benchmark_version": "0.1-draft",
    "status": "SMOKE_TEST_ONLY_NOT_A_HELD_OUT_BENCHMARK",
    "annotation_status": "machine_assisted_draft_not_expert_validated",
    "document_id": "bam-s005c-v2",
    "pdf_sha256": "a556ad0b36a5eb75ba706ceb37c51412be4ca2f3b5a0d39085b32f37bb2204b9",
    "data_summary": {
      "documents": 1,
      "pages": 8,
      "extraction_records": 27,
      "queries": 16,
      "research_papers": 0
    },
    "warning": "Visible single certificate; draft labels; template-specific extraction; page-level retrieval; no generalization or model-ranking claim.",
    "environment": {
      "bun": "1.3.14",
      "platform": "linux",
      "arch": "x64",
      "cpu": "AMD EPYC",
      "poppler": "pdftotext version 22.12.0\nCopyright 2005-2022 The Poppler Developers - http://poppler.freedesktop.org\nCopyright 1996-2011, 2022 Glyph & Cog, LLC"
    },
    "timing_notes": "One local run. Extraction time includes PDF text decoding. Retrieval time excludes text decoding. Not hardware-comparable performance estimates.",
    "extraction": {
      "baseline": "poppler_layout_summary_regex_visible_template",
      "extraction_ms": 490.8215560000003,
      "gold_records": 27,
      "predicted_records": 27,
      "exact_records": 27,
      "record_precision": 1,
      "record_recall": 1,
      "record_f1": 1,
      "field_accuracy_over_all_gold_records": {
        "value": 1,
        "unit": 1,
        "expanded_uncertainty": 1,
        "coverage_factor": 1,
        "status": 1,
        "oxide_formula": 1,
        "oxide_value": 1,
        "source_page": 1
      },
      "extra_elements": [],
      "errors": []
    },
    "retrieval": [
      {
        "baseline": "bm25",
        "parameters": {
          "k1": 1.2,
          "b": 0.75
        },
        "retrieval_ms": 4.48970700000018,
        "query_count": 16,
        "submitted_queries": 16,
        "aggregate": {
          "recall_at_1": 0.7083333333333333,
          "mrr_at_1": 0.8125,
          "ndcg_at_1": 0.8125,
          "complete_evidence_at_1": 0.625,
          "recall_at_3": 0.8854166666666667,
          "mrr_at_3": 0.8645833333333334,
          "ndcg_at_3": 0.8393223982796078,
          "complete_evidence_at_3": 0.8125,
          "recall_at_5": 1,
          "mrr_at_5": 0.8802083333333334,
          "ndcg_at_5": 0.8936962493635601,
          "complete_evidence_at_5": 1
        },
        "by_category": {
          "table_lookup": {
            "recall_at_1": 0.6666666666666666,
            "mrr_at_1": 0.6666666666666666,
            "ndcg_at_1": 0.6666666666666666,
            "complete_evidence_at_1": 0.6666666666666666,
            "recall_at_3": 1,
            "mrr_at_3": 0.7777777777777778,
            "ndcg_at_3": 0.8333333333333334,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 0.7777777777777778,
            "ndcg_at_5": 0.8333333333333334,
            "complete_evidence_at_5": 1
          },
          "qualification": {
            "recall_at_1": 0.6666666666666666,
            "mrr_at_1": 0.6666666666666666,
            "ndcg_at_1": 0.6666666666666666,
            "complete_evidence_at_1": 0.6666666666666666,
            "recall_at_3": 1,
            "mrr_at_3": 0.8333333333333334,
            "ndcg_at_3": 0.8769765845238191,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 0.8333333333333334,
            "ndcg_at_5": 0.8769765845238191,
            "complete_evidence_at_5": 1
          },
          "cross_page": {
            "recall_at_1": 0.41666666666666663,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 0,
            "recall_at_3": 0.5833333333333333,
            "mrr_at_3": 1,
            "ndcg_at_3": 0.68925391487704,
            "complete_evidence_at_3": 0,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 0.908906444511962,
            "complete_evidence_at_5": 1
          },
          "provenance": {
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          "usage": {
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          "method": {
            "recall_at_1": 0.25,
            "mrr_at_1": 0.5,
            "ndcg_at_1": 0.5,
            "complete_evidence_at_1": 0,
            "recall_at_3": 0.5,
            "mrr_at_3": 0.5,
            "ndcg_at_3": 0.4598603945740938,
            "complete_evidence_at_3": 0.5,
            "recall_at_5": 1,
            "mrr_at_5": 0.625,
            "ndcg_at_5": 0.6751986736107903,
            "complete_evidence_at_5": 1
          }
        },
        "per_query": [
          {
            "id": "Q01",
            "category": "table_lookup",
            "ranking": [
              1,
              2,
              3,
              4,
              8,
              5,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q02",
            "category": "qualification",
            "ranking": [
              2,
              1,
              4,
              8,
              3,
              5,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q03",
            "category": "table_lookup",
            "ranking": [
              1,
              2,
              8,
              4,
              3,
              5,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q04",
            "category": "qualification",
            "ranking": [
              1,
              2,
              4,
              3,
              8,
              5,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q05",
            "category": "cross_page",
            "ranking": [
              4,
              1,
              2,
              3,
              8,
              6,
              5,
              7
            ],
            "recall_at_1": 0.3333333333333333,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 0,
            "recall_at_3": 0.6666666666666666,
            "mrr_at_3": 1,
            "ndcg_at_3": 0.7653606369886218,
            "complete_evidence_at_3": 0,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 0.9674679834891694,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q06",
            "category": "provenance",
            "ranking": [
              8,
              2,
              1,
              4,
              3,
              5,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q07",
            "category": "usage",
            "ranking": [
              2,
              8,
              1,
              3,
              4,
              5,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q08",
            "category": "usage",
            "ranking": [
              2,
              8,
              1,
              3,
              4,
              5,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q09",
            "category": "provenance",
            "ranking": [
              8,
              1,
              2,
              4,
              3,
              5,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q10",
            "category": "method",
            "ranking": [
              5,
              1,
              8,
              2,
              4,
              3,
              7,
              6
            ],
            "recall_at_1": 0.5,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 0,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 0.9197207891481876,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 0.9197207891481876,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q11",
            "category": "method",
            "ranking": [
              5,
              8,
              2,
              7,
              4,
              6,
              1,
              3
            ],
            "recall_at_1": 0,
            "mrr_at_1": 0,
            "ndcg_at_1": 0,
            "complete_evidence_at_1": 0,
            "recall_at_3": 0,
            "mrr_at_3": 0,
            "ndcg_at_3": 0,
            "complete_evidence_at_3": 0,
            "recall_at_5": 1,
            "mrr_at_5": 0.25,
            "ndcg_at_5": 0.4306765580733931,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q12",
            "category": "usage",
            "ranking": [
              2,
              8,
              1,
              3,
              4,
              5,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q13",
            "category": "table_lookup",
            "ranking": [
              8,
              4,
              1,
              2,
              5,
              3,
              6,
              7
            ],
            "recall_at_1": 0,
            "mrr_at_1": 0,
            "ndcg_at_1": 0,
            "complete_evidence_at_1": 0,
            "recall_at_3": 1,
            "mrr_at_3": 0.3333333333333333,
            "ndcg_at_3": 0.5,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 0.3333333333333333,
            "ndcg_at_5": 0.5,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q14",
            "category": "cross_page",
            "ranking": [
              2,
              8,
              4,
              7,
              1,
              3,
              5,
              6
            ],
            "recall_at_1": 0.5,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 0,
            "recall_at_3": 0.5,
            "mrr_at_3": 1,
            "ndcg_at_3": 0.6131471927654584,
            "complete_evidence_at_3": 0,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 0.8503449055347546,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q15",
            "category": "qualification",
            "ranking": [
              8,
              1,
              2,
              3,
              4,
              5,
              6,
              7
            ],
            "recall_at_1": 0,
            "mrr_at_1": 0,
            "ndcg_at_1": 0,
            "complete_evidence_at_1": 0,
            "recall_at_3": 1,
            "mrr_at_3": 0.5,
            "ndcg_at_3": 0.6309297535714574,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 0.5,
            "ndcg_at_5": 0.6309297535714574,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q16",
            "category": "provenance",
            "ranking": [
              8,
              1,
              2,
              4,
              3,
              5,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          }
        ]
      },
      {
        "baseline": "tfidf",
        "parameters": {
          "tf": "1+ln(f)",
          "idf": "ln((N+1)/(df+1))+1",
          "normalization": "cosine",
          "query_tf": "binary"
        },
        "retrieval_ms": 1.429555000000164,
        "query_count": 16,
        "submitted_queries": 16,
        "aggregate": {
          "recall_at_1": 0.7395833333333333,
          "mrr_at_1": 0.8125,
          "ndcg_at_1": 0.8125,
          "complete_evidence_at_1": 0.6875,
          "recall_at_3": 0.9166666666666667,
          "mrr_at_3": 0.90625,
          "ndcg_at_3": 0.876701259008221,
          "complete_evidence_at_3": 0.8125,
          "recall_at_5": 0.96875,
          "mrr_at_5": 0.90625,
          "ndcg_at_5": 0.9041578252125863,
          "complete_evidence_at_5": 0.9375
        },
        "by_category": {
          "table_lookup": {
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          "qualification": {
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          "cross_page": {
            "recall_at_1": 0.16666666666666666,
            "mrr_at_1": 0.5,
            "ndcg_at_1": 0.5,
            "complete_evidence_at_1": 0,
            "recall_at_3": 0.5833333333333333,
            "mrr_at_3": 0.75,
            "ndcg_at_3": 0.5761067221115816,
            "complete_evidence_at_3": 0,
            "recall_at_5": 1,
            "mrr_at_5": 0.75,
            "ndcg_at_5": 0.7957592517465035,
            "complete_evidence_at_5": 1
          },
          "provenance": {
            "recall_at_1": 0.6666666666666666,
            "mrr_at_1": 0.6666666666666666,
            "ndcg_at_1": 0.6666666666666666,
            "complete_evidence_at_1": 0.6666666666666666,
            "recall_at_3": 1,
            "mrr_at_3": 0.8333333333333334,
            "ndcg_at_3": 0.8769765845238191,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 0.8333333333333334,
            "ndcg_at_5": 0.8769765845238191,
            "complete_evidence_at_5": 1
          },
          "usage": {
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          "method": {
            "recall_at_1": 0.25,
            "mrr_at_1": 0.5,
            "ndcg_at_1": 0.5,
            "complete_evidence_at_1": 0,
            "recall_at_3": 0.75,
            "mrr_at_3": 0.75,
            "ndcg_at_3": 0.6220384731684578,
            "complete_evidence_at_3": 0.5,
            "recall_at_5": 0.75,
            "mrr_at_5": 0.75,
            "ndcg_at_5": 0.6220384731684578,
            "complete_evidence_at_5": 0.5
          }
        },
        "per_query": [
          {
            "id": "Q01",
            "category": "table_lookup",
            "ranking": [
              1,
              2,
              3,
              4,
              8,
              5,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q02",
            "category": "qualification",
            "ranking": [
              2,
              1,
              4,
              8,
              3,
              5,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q03",
            "category": "table_lookup",
            "ranking": [
              1,
              2,
              8,
              4,
              3,
              5,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q04",
            "category": "qualification",
            "ranking": [
              1,
              2,
              4,
              3,
              8,
              5,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q05",
            "category": "cross_page",
            "ranking": [
              4,
              1,
              2,
              3,
              8,
              6,
              5,
              7
            ],
            "recall_at_1": 0.3333333333333333,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 0,
            "recall_at_3": 0.6666666666666666,
            "mrr_at_3": 1,
            "ndcg_at_3": 0.7653606369886218,
            "complete_evidence_at_3": 0,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 0.9674679834891694,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q06",
            "category": "provenance",
            "ranking": [
              2,
              8,
              1,
              4,
              3,
              5,
              6,
              7
            ],
            "recall_at_1": 0,
            "mrr_at_1": 0,
            "ndcg_at_1": 0,
            "complete_evidence_at_1": 0,
            "recall_at_3": 1,
            "mrr_at_3": 0.5,
            "ndcg_at_3": 0.6309297535714574,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 0.5,
            "ndcg_at_5": 0.6309297535714574,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q07",
            "category": "usage",
            "ranking": [
              2,
              8,
              1,
              3,
              4,
              5,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q08",
            "category": "usage",
            "ranking": [
              2,
              8,
              1,
              3,
              4,
              5,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q09",
            "category": "provenance",
            "ranking": [
              8,
              1,
              4,
              2,
              3,
              5,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q10",
            "category": "method",
            "ranking": [
              5,
              7,
              6,
              1,
              4,
              8,
              3,
              2
            ],
            "recall_at_1": 0.5,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 0,
            "recall_at_3": 0.5,
            "mrr_at_3": 1,
            "ndcg_at_3": 0.6131471927654584,
            "complete_evidence_at_3": 0,
            "recall_at_5": 0.5,
            "mrr_at_5": 1,
            "ndcg_at_5": 0.6131471927654584,
            "complete_evidence_at_5": 0
          },
          {
            "id": "Q11",
            "category": "method",
            "ranking": [
              5,
              7,
              8,
              6,
              2,
              4,
              1,
              3
            ],
            "recall_at_1": 0,
            "mrr_at_1": 0,
            "ndcg_at_1": 0,
            "complete_evidence_at_1": 0,
            "recall_at_3": 1,
            "mrr_at_3": 0.5,
            "ndcg_at_3": 0.6309297535714574,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 0.5,
            "ndcg_at_5": 0.6309297535714574,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q12",
            "category": "usage",
            "ranking": [
              2,
              8,
              1,
              3,
              4,
              5,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q13",
            "category": "table_lookup",
            "ranking": [
              1,
              8,
              4,
              5,
              2,
              3,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q14",
            "category": "cross_page",
            "ranking": [
              7,
              1,
              8,
              4,
              2,
              3,
              5,
              6
            ],
            "recall_at_1": 0,
            "mrr_at_1": 0,
            "ndcg_at_1": 0,
            "complete_evidence_at_1": 0,
            "recall_at_3": 0.5,
            "mrr_at_3": 0.5,
            "ndcg_at_3": 0.3868528072345416,
            "complete_evidence_at_3": 0,
            "recall_at_5": 1,
            "mrr_at_5": 0.5,
            "ndcg_at_5": 0.6240505200038378,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q15",
            "category": "qualification",
            "ranking": [
              1,
              8,
              2,
              3,
              4,
              5,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          },
          {
            "id": "Q16",
            "category": "provenance",
            "ranking": [
              8,
              1,
              2,
              4,
              3,
              5,
              6,
              7
            ],
            "recall_at_1": 1,
            "mrr_at_1": 1,
            "ndcg_at_1": 1,
            "complete_evidence_at_1": 1,
            "recall_at_3": 1,
            "mrr_at_3": 1,
            "ndcg_at_3": 1,
            "complete_evidence_at_3": 1,
            "recall_at_5": 1,
            "mrr_at_5": 1,
            "ndcg_at_5": 1,
            "complete_evidence_at_5": 1
          }
        ]
      }
    ]
  },
  "manifest": {
    "schema_version": "0.1",
    "document_id": "bam-s005c-v2",
    "family_id": "bam-s005-series",
    "filename": "Zertifikat_BAM-S005c_rev1.pdf",
    "document_version": "V2",
    "accepted_date": "2020-08-19",
    "revision_date": "2025-03-03",
    "version_evidence_page": 8,
    "validity": "Until revocation by the producer, as stated on page 1 of the uploaded V2 file",
    "page_count": 8,
    "language": "en",
    "source_url_candidate": "https://webshop.bam.de/media/wysiwyg/Kategorien/Referenzmaterialien/Glaeser/Chemische_Zusammensetzung/Zertifikate/Zertifikat_BAM-S005c_rev1.pdf",
    "source_url_note": "Official candidate URL identified by public source research. The evaluated bytes are the user upload, not a downloaded remote copy; equality to the current URL is not asserted.",
    "acquisition": "user_upload",
    "rights_status": "public_access_confirmed_redistribution_permission_unverified",
    "split": "development_smoke_test_only",
    "annotation_status": "machine_assisted_draft_not_expert_validated",
    "sha256": "a556ad0b36a5eb75ba706ceb37c51412be4ca2f3b5a0d39085b32f37bb2204b9"
  },
  "extraction": {
    "schema_version": "0.1",
    "annotation_status": "machine_assisted_draft_not_expert_validated",
    "document_id": "bam-s005c-v2",
    "scope": "Elemental mass-fraction rows in the summary tables on PDF pages 1 and 2 only; exclude individual laboratory results and methods.",
    "records": [
      {
        "element": "Al",
        "value": "0.587",
        "unit": "%",
        "expanded_uncertainty": "0.018",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "Al2O3",
        "oxide_value": "1.109",
        "source_page": 1
      },
      {
        "element": "Ca",
        "value": "7.43",
        "unit": "%",
        "expanded_uncertainty": "0.12",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "CaO",
        "oxide_value": "10.39",
        "source_page": 1
      },
      {
        "element": "K",
        "value": "0.595",
        "unit": "%",
        "expanded_uncertainty": "0.014",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "K2O",
        "oxide_value": "0.717",
        "source_page": 1
      },
      {
        "element": "Mg",
        "value": "1.37",
        "unit": "%",
        "expanded_uncertainty": "0.04",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "MgO",
        "oxide_value": "2.28",
        "source_page": 1
      },
      {
        "element": "Na",
        "value": "10.33",
        "unit": "%",
        "expanded_uncertainty": "0.24",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "Na2O",
        "oxide_value": "13.92",
        "source_page": 1
      },
      {
        "element": "Si",
        "value": "33.1",
        "unit": "%",
        "expanded_uncertainty": "0.5",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "SiO2",
        "oxide_value": "70.8",
        "source_page": 1
      },
      {
        "element": "As",
        "value": "81",
        "unit": "mg/kg",
        "expanded_uncertainty": "4",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "As2O3",
        "oxide_value": "107",
        "source_page": 1
      },
      {
        "element": "Ba",
        "value": "102",
        "unit": "mg/kg",
        "expanded_uncertainty": "4",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "BaO",
        "oxide_value": "114",
        "source_page": 1
      },
      {
        "element": "Cd",
        "value": "47",
        "unit": "mg/kg",
        "expanded_uncertainty": "4",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "CdO",
        "oxide_value": "54",
        "source_page": 1
      },
      {
        "element": "Ce",
        "value": "80",
        "unit": "mg/kg",
        "expanded_uncertainty": "5",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "CeO2",
        "oxide_value": "98",
        "source_page": 1
      },
      {
        "element": "Co",
        "value": "33.2",
        "unit": "mg/kg",
        "expanded_uncertainty": "1.9",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "CoO",
        "oxide_value": "42.3",
        "source_page": 1
      },
      {
        "element": "Cr",
        "value": "10.8",
        "unit": "mg/kg",
        "expanded_uncertainty": "1.0",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "Cr2O3",
        "oxide_value": "15.8",
        "source_page": 1
      },
      {
        "element": "Cu",
        "value": "86",
        "unit": "mg/kg",
        "expanded_uncertainty": "5",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "CuO",
        "oxide_value": "107",
        "source_page": 1
      },
      {
        "element": "Fe",
        "value": "295",
        "unit": "mg/kg",
        "expanded_uncertainty": "7",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "Fe2O3",
        "oxide_value": "422",
        "source_page": 1
      },
      {
        "element": "Mn",
        "value": "69.6",
        "unit": "mg/kg",
        "expanded_uncertainty": "2.5",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "MnO",
        "oxide_value": "89.9",
        "source_page": 1
      },
      {
        "element": "Mo",
        "value": "215",
        "unit": "mg/kg",
        "expanded_uncertainty": "7",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "MoO3",
        "oxide_value": "323",
        "source_page": 1
      },
      {
        "element": "Ni",
        "value": "41.3",
        "unit": "mg/kg",
        "expanded_uncertainty": "1.7",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "NiO",
        "oxide_value": "52.6",
        "source_page": 1
      },
      {
        "element": "Pb",
        "value": "182",
        "unit": "mg/kg",
        "expanded_uncertainty": "8",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "PbO",
        "oxide_value": "196",
        "source_page": 1
      },
      {
        "element": "Sb",
        "value": "103",
        "unit": "mg/kg",
        "expanded_uncertainty": "4",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "Sb2O3",
        "oxide_value": "123",
        "source_page": 1
      },
      {
        "element": "Sn",
        "value": "72.9",
        "unit": "mg/kg",
        "expanded_uncertainty": "2.3",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "SnO2",
        "oxide_value": "92.5",
        "source_page": 1
      },
      {
        "element": "Sr",
        "value": "134",
        "unit": "mg/kg",
        "expanded_uncertainty": "6",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "SrO",
        "oxide_value": "158",
        "source_page": 1
      },
      {
        "element": "Ti",
        "value": "101",
        "unit": "mg/kg",
        "expanded_uncertainty": "6",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "TiO2",
        "oxide_value": "169",
        "source_page": 1
      },
      {
        "element": "V",
        "value": "189",
        "unit": "mg/kg",
        "expanded_uncertainty": "8",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "V2O5",
        "oxide_value": "337",
        "source_page": 1
      },
      {
        "element": "Zn",
        "value": "157",
        "unit": "mg/kg",
        "expanded_uncertainty": "6",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "ZnO",
        "oxide_value": "196",
        "source_page": 1
      },
      {
        "element": "Zr",
        "value": "544",
        "unit": "mg/kg",
        "expanded_uncertainty": "26",
        "coverage_factor": 2,
        "status": "certified",
        "oxide_formula": "ZrO2",
        "oxide_value": "735",
        "source_page": 1
      },
      {
        "element": "P",
        "value": "8.3",
        "unit": "mg/kg",
        "expanded_uncertainty": "2.5",
        "coverage_factor": 2,
        "status": "information_only",
        "oxide_formula": "P2O5",
        "oxide_value": "19.0",
        "source_page": 2
      },
      {
        "element": "Se",
        "value": "2.5",
        "unit": "mg/kg",
        "expanded_uncertainty": "0.8",
        "coverage_factor": 2,
        "status": "information_only",
        "oxide_formula": null,
        "oxide_value": null,
        "source_page": 2
      }
    ],
    "notes": "Elemental mass fractions and expanded uncertainties are transcribed from the summary tables; all uncertainties use k=2 (approximately 95% confidence). Bracketed oxide values are calculated from elemental mass fractions using molar masses and are not independent certified measurands. Page 1 rows are certified; P and Se on page 2 are information-only because inter-laboratory certification uncertainty was too large. Values are draft machine-assisted annotations and are not BAM-expert-validated gold labels."
  },
  "retrieval": {
    "schema_version": "0.1",
    "annotation_status": "machine_assisted_draft_not_expert_validated",
    "document_id": "bam-s005c-v2",
    "evaluation_unit": "page",
    "queries": [
      {
        "id": "Q01",
        "query": "What certified elemental mass fraction and expanded uncertainty are reported for Al?",
        "category": "table_lookup",
        "expected_answer": "Al: 0.587%, expanded uncertainty 0.018% (k=2).",
        "evidence_pages": [
          1
        ],
        "relevance": {
          "1": 2
        }
      },
      {
        "id": "Q02",
        "query": "Which two elements are listed as values for information, and what are their elemental mass fractions?",
        "category": "qualification",
        "expected_answer": "P: 8.3 mg/kg; Se: 2.5 mg/kg; both are information-only.",
        "evidence_pages": [
          2
        ],
        "relevance": {
          "2": 2
        }
      },
      {
        "id": "Q03",
        "query": "For Si on the certified summary, what are the elemental and calculated oxide quantities?",
        "category": "table_lookup",
        "expected_answer": "Si: 33.1% elemental; calculated SiO2: 70.8%.",
        "evidence_pages": [
          1
        ],
        "relevance": {
          "1": 2
        }
      },
      {
        "id": "Q04",
        "query": "What coverage factor and approximate confidence level apply to the certified mass-fraction uncertainties?",
        "category": "qualification",
        "expected_answer": "k=2, corresponding to approximately 95% confidence.",
        "evidence_pages": [
          1
        ],
        "relevance": {
          "1": 2
        }
      },
      {
        "id": "Q05",
        "query": "What are the certified Fe mass fraction and the mean of its accepted laboratory means, and what does the certificate say about omitted outlying values?",
        "category": "cross_page",
        "expected_answer": "The certified Fe value is 295 mg/kg (p1); p3–4 show accepted laboratory data and M (mean of laboratory means), with Fe M=295 mg/kg, after statistical examination/outlier handling.",
        "evidence_pages": [
          1,
          3,
          4
        ],
        "relevance": {
          "1": 2,
          "3": 2,
          "4": 2
        }
      },
      {
        "id": "Q06",
        "query": "What certificate revision information is given, including the acceptance and revision dates?",
        "category": "provenance",
        "expected_answer": "Accepted as BAM-CRM 2020-08-19; revised 2025-03-03; certificate is BAM-S005c V2.",
        "evidence_pages": [
          8
        ],
        "relevance": {
          "8": 2
        }
      },
      {
        "id": "Q07",
        "query": "What is the recommended use of this CRM?",
        "category": "usage",
        "expected_answer": "Establishing or checking calibration of X-ray spectrometers for samples of similar matrix composition.",
        "evidence_pages": [
          2
        ],
        "relevance": {
          "2": 2
        }
      },
      {
        "id": "Q08",
        "query": "What minimum sample size is specified for wet chemical analysis?",
        "category": "usage",
        "expected_answer": "0.2 g.",
        "evidence_pages": [
          2
        ],
        "relevance": {
          "2": 2
        }
      },
      {
        "id": "Q09",
        "query": "How is metrological traceability of the certified mass fractions to the SI ensured?",
        "category": "provenance",
        "expected_answer": "By calibration using standard solutions from pure metals or stoichiometric compounds, checked commercial calibration solutions, other CRMs, or reference materials.",
        "evidence_pages": [
          8
        ],
        "relevance": {
          "8": 2
        }
      },
      {
        "id": "Q10",
        "query": "What method was used for Al line 6, and what does that method abbreviation mean?",
        "category": "method",
        "expected_answer": "FAAS; flame atomic absorption spectrometry.",
        "evidence_pages": [
          5,
          8
        ],
        "relevance": {
          "5": 2,
          "8": 2
        }
      },
      {
        "id": "Q11",
        "query": "Which analytical method was used for Se line 5?",
        "category": "method",
        "expected_answer": "ICP-MS.",
        "evidence_pages": [
          7
        ],
        "relevance": {
          "7": 2
        }
      },
      {
        "id": "Q12",
        "query": "What physical form and approximate dimensions are given for the reference material?",
        "category": "usage",
        "expected_answer": "Discs, approximately 38 mm diameter and 4 mm height.",
        "evidence_pages": [
          2
        ],
        "relevance": {
          "2": 2
        }
      },
      {
        "id": "Q13",
        "query": "Which units are used for the certified elemental rows in the summary table?",
        "category": "table_lookup",
        "expected_answer": "% for Al, Ca, K, Mg, Na and Si; mg/kg for the remaining certified elements.",
        "evidence_pages": [
          1
        ],
        "relevance": {
          "1": 2
        }
      },
      {
        "id": "Q14",
        "query": "Compare the qualification of the certified summary rows with P and Se, and explain why the certificate treats them differently.",
        "category": "cross_page",
        "expected_answer": "Page 1 rows are certified values; P and Se on page 2 are information-only because inter-laboratory certification uncertainty was too large.",
        "evidence_pages": [
          1,
          2
        ],
        "relevance": {
          "1": 2,
          "2": 2
        }
      },
      {
        "id": "Q15",
        "query": "What does the certificate say about its validity period?",
        "category": "qualification",
        "expected_answer": "It remains valid until revoked by the producer of the material.",
        "evidence_pages": [
          1
        ],
        "relevance": {
          "1": 2
        }
      },
      {
        "id": "Q16",
        "query": "Which organization is identified as the producer offering this reference material, and where is it located?",
        "category": "provenance",
        "expected_answer": "Bundesanstalt für Materialforschung und -prüfung (BAM), Richard-Willstätter-Str. 11, 12489 Berlin.",
        "evidence_pages": [
          8
        ],
        "relevance": {
          "8": 2
        }
      }
    ]
  }
};
