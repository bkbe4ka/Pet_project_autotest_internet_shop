from .base import Candidate, ElementDescriptor, Strategy
from .attr_weighted import AttrWeightedStrategy
from .structural import StructuralStrategy
from .embedding_match import EmbeddingStrategy, get_embedder

__all__ = [
    "Candidate", "ElementDescriptor", "Strategy",
    "AttrWeightedStrategy", "StructuralStrategy", "EmbeddingStrategy",
    "get_embedder",
]
