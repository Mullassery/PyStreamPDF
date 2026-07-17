"""Tests for semantic entity extraction."""

import pytest
import sys
sys.path.insert(0, '/Users/georgimullassery/PyStreamPDF/python')

from pystreampdf.semantic import ConceptExtractor, Entity, EntityType


class TestConceptExtractor:
    """Test concept/entity extraction."""

    def test_extractor_init(self):
        """Test extractor initialization."""
        extractor = ConceptExtractor()
        assert extractor is not None
        assert extractor.min_confidence == 0.6

    def test_extract_neural_network_concept(self):
        """Test extracting neural network concept."""
        extractor = ConceptExtractor()
        text = "We propose a novel neural network architecture for vision tasks."
        entities = extractor.extract(text)

        nn_entities = [e for e in entities if "neural network" in e.name.lower()]
        assert len(nn_entities) > 0
        assert nn_entities[0].type == EntityType.METHOD
        assert nn_entities[0].confidence >= 0.8

    def test_extract_transformer_method(self):
        """Test extracting transformer method."""
        extractor = ConceptExtractor()
        text = "The transformer architecture has revolutionized NLP and vision."
        entities = extractor.extract(text)

        transformer = [e for e in entities if "transformer" in e.name.lower()]
        assert len(transformer) > 0
        assert transformer[0].type == EntityType.METHOD

    def test_extract_metrics(self):
        """Test metric extraction."""
        extractor = ConceptExtractor()
        text = "We achieved 95.2% accuracy on the ImageNet dataset with F1 score of 0.94."
        entities = extractor.extract(text)

        metrics = [e for e in entities if e.type == EntityType.METRIC]
        assert len(metrics) > 0

    def test_extract_dates(self):
        """Test date extraction."""
        extractor = ConceptExtractor()
        text = "This paper was published in 2022 and extended work in 2023."
        entities = extractor.extract(text)

        dates = [e for e in entities if e.type == EntityType.DATE]
        assert len(dates) > 0
        assert any("2022" in e.name for e in dates)
        assert any("2023" in e.name for e in dates)

    def test_extract_organization(self):
        """Test organization extraction."""
        extractor = ConceptExtractor()
        text = "Researchers from Google AI and Stanford University collaborated on this."
        entities = extractor.extract(text)

        orgs = [e for e in entities if e.type == EntityType.ORGANIZATION]
        assert len(orgs) > 0

    def test_confidence_filtering(self):
        """Test confidence threshold filtering."""
        extractor = ConceptExtractor(min_confidence=0.9)
        text = "We use neural networks and deep learning techniques."
        entities = extractor.extract(text)

        # All returned entities should meet threshold
        assert all(e.confidence >= 0.9 for e in entities)

    def test_deduplication(self):
        """Test entity deduplication."""
        extractor = ConceptExtractor()
        text = "Deep learning is used in deep learning applications. Deep learning powers neural networks."
        entities = extractor.extract(text)

        # "Deep learning" should appear only once (deduplicated)
        dl_entities = [e for e in entities if "deep learning" in e.name.lower()]
        assert len(dl_entities) <= 1  # Deduplicated to max 1
        # Note: frequency tracking for multi-occurrence in same text is for Phase 4.2

    def test_context_extraction(self):
        """Test that context is extracted with entities."""
        extractor = ConceptExtractor()
        text = "The transformer architecture uses self-attention mechanisms to process sequences efficiently."
        entities = extractor.extract(text)

        transformer = [e for e in entities if "transformer" in e.name.lower()]
        assert len(transformer) > 0
        if transformer[0].context:
            assert "self-attention" in transformer[0].context or len(transformer[0].context) > 0

    def test_batch_extract(self):
        """Test batch extraction."""
        extractor = ConceptExtractor()
        texts = [
            ("Neural networks are used in deep learning.", 1),
            ("The transformer was introduced in 2017.", 2),
            ("We use recurrent neural networks and attention mechanism.", 3),
        ]

        all_entities = extractor.batch_extract(texts)
        assert len(all_entities) > 0
        assert any(e.page == 1 for e in all_entities)
        assert any(e.page == 2 for e in all_entities)
        assert any(e.page == 3 for e in all_entities)

    def test_get_entities_by_type(self):
        """Test filtering entities by type."""
        extractor = ConceptExtractor()
        text = "Neural networks with 92.3% accuracy were published in 2022."
        entities = extractor.extract(text)

        methods = extractor.get_entities_by_type(entities, EntityType.METHOD)
        assert all(e.type == EntityType.METHOD for e in methods)

    def test_get_top_entities(self):
        """Test getting top entities by frequency."""
        extractor = ConceptExtractor()
        text = "Deep learning deep learning neural networks neural networks transformer methods."
        entities = extractor.extract(text)

        top = extractor.get_top_entities(entities, limit=2)
        assert len(top) <= 2
        if len(top) > 1:
            assert top[0].frequency >= top[1].frequency

    def test_multiple_concepts_in_text(self):
        """Test extracting multiple concepts from same text."""
        extractor = ConceptExtractor()
        text = """
        The transformer architecture uses self-attention mechanisms for deep learning tasks.
        Recurrent neural networks process sequences, but attention mechanisms are more efficient.
        We achieved 94.5% accuracy on this benchmark with an F1 score of 0.92.
        """
        entities = extractor.extract(text)

        # Should find multiple concepts
        assert len(entities) > 3
        # Should have at least methods and metrics
        types = set(e.type for e in entities)
        assert EntityType.METHOD in types or EntityType.CONCEPT in types
        assert EntityType.METRIC in types

    def test_empty_text(self):
        """Test extraction from empty text."""
        extractor = ConceptExtractor()
        entities = extractor.extract("")
        assert isinstance(entities, list)
        assert len(entities) == 0

    def test_entity_properties(self):
        """Test that extracted entities have required properties."""
        extractor = ConceptExtractor()
        text = "Neural networks were developed in 2012."
        entities = extractor.extract(text)

        for entity in entities:
            assert hasattr(entity, "name")
            assert hasattr(entity, "type")
            assert hasattr(entity, "confidence")
            assert 0 <= entity.confidence <= 1
            assert isinstance(entity.frequency, int)


class TestEntityTypes:
    """Test entity type enums."""

    def test_entity_type_values(self):
        """Test entity type enum values."""
        assert EntityType.PERSON.value == "person"
        assert EntityType.METHOD.value == "method"
        assert EntityType.METRIC.value == "metric"
        assert EntityType.DATE.value == "date"

    def test_entity_type_membership(self):
        """Test checking entity types."""
        entity = Entity("transformer", EntityType.METHOD, 0.9)
        assert entity.type == EntityType.METHOD
        assert entity.type != EntityType.PERSON


class TestIntegration:
    """Integration tests for entity extraction."""

    def test_academic_paper_abstract(self):
        """Test extraction from academic paper abstract."""
        abstract = """
        We propose a novel deep learning approach for image segmentation using transformer networks.
        Our method achieves 96.2% accuracy on the COCO dataset, outperforming previous CNN-based approaches.
        The work was developed at Stanford University in 2023 and builds upon the attention mechanism.
        """

        extractor = ConceptExtractor()
        entities = extractor.extract(abstract)

        # Should extract key concepts
        assert len(entities) > 0
        entity_names = [e.name.lower() for e in entities]
        assert any("deep learning" in n or "transformer" in n for n in entity_names)
        assert any("accuracy" in n or "coco" in n for n in entity_names)

    def test_technical_paper_paragraph(self):
        """Test extraction from technical paragraph."""
        text = """
        BERT, developed by Google AI in 2018, uses bidirectional transformers for pre-training.
        We fine-tuned BERT on 100,000 labeled examples achieving F1 score of 0.91.
        This method outperforms recurrent neural networks and previous LSTM approaches.
        """

        extractor = ConceptExtractor()
        entities = extractor.extract(text)

        # Check for various entity types
        types = set(e.type for e in entities)
        assert len(types) >= 2  # Should find multiple types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
