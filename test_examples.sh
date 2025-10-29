#!/bin/bash
# Quick test examples for the pipeline stages

echo "=========================================="
echo "Pipeline Stage Testing - Quick Examples"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Available Test Commands:${NC}"
echo ""

echo "1. Test all stages for Article 1:"
echo "   python3 test_pipeline_stages.py --stage all --article 1 --verbose"
echo ""

echo "2. Test just article parsing:"
echo "   python3 test_pipeline_stages.py --stage 1"
echo ""

echo "3. Test NLP pipeline for Article 2:"
echo "   python3 test_pipeline_stages.py --stage 2 --article 2 --verbose"
echo ""

echo "4. Test event extraction for all articles:"
echo "   python3 test_pipeline_stages.py --stage 3 --verbose"
echo ""

echo "5. Generate CSV output:"
echo "   python3 test_pipeline_stages.py --stage 5"
echo ""

echo -e "${BLUE}Quick Individual Component Tests:${NC}"
echo ""

echo "6. Test date normalization:"
echo "   python3 -c \"from utils.date_normalizer import DateNormalizer; n = DateNormalizer(); print(n.normalize_date('Friday', 'March 15, 2024'))\""
echo ""

echo "7. Test taxonomy classification:"
echo "   python3 -c \"from taxonomy_classifier import TaxonomyClassifier; c = TaxonomyClassifier(); event = {'trigger': {'lemma': 'attack'}, 'who': {'text': 'Al-Shabaab', 'type': 'TERRORIST'}, 'how': {'tactics': ['suicide']}}; print(c.classify(event))\""
echo ""

echo -e "${BLUE}View Results:${NC}"
echo ""

echo "8. View parsed articles:"
echo "   cat output/stage1_parsed_articles.json | python3 -m json.tool | head -50"
echo ""

echo "9. View extracted events:"
echo "   cat output/stage3_extracted_events.json | python3 -m json.tool"
echo ""

echo "10. View CSV output:"
echo "   cat output/test_extracted_events.csv | column -t -s, | head"
echo ""

echo -e "${GREEN}Ready to test! Run any command above.${NC}"
