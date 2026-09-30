import unittest
from app.models.document import Document
from app.services.bm25_store import BM25Store
from app.services.code_chunker import chunk_python_file
from app.services.prompt_builder import build_prompt, format_document_context


class TestServices(unittest.TestCase):

    def test_bm25_store_incremental_tokenization(self):
        store = BM25Store()
        doc1 = Document(page_content="def hello(): return 'world'")
        doc2 = Document(page_content="class ArchonAI: pass")
        doc3 = Document(page_content="def footer(): return 'copyright'")

        store.add([doc1])
        self.assertEqual(len(store.documents), 1)
        self.assertEqual(len(store.corpus), 1)

        store.add([doc2, doc3])
        self.assertEqual(len(store.documents), 3)
        self.assertEqual(len(store.corpus), 3)

        results = store.search("ArchonAI", top_k=1)
        self.assertEqual(len(results), 1)
        self.assertIn("ArchonAI", results[0]["document"].page_content)


    def test_code_chunker_captures_module_header_and_ast(self):
        sample_code = (
            "import os\n"
            "from app.core import config\n\n"
            "GLOBAL_VAR = 'test'\n\n"
            "def sample_func():\n"
            "    return True\n"
        )
        chunks = chunk_python_file(sample_code, {"source": "sample.py"})

        # Should produce 2 chunks: 1 module_header and 1 sample_func
        self.assertGreaterEqual(len(chunks), 2)

        header_chunk = chunks[0]
        self.assertEqual(header_chunk.metadata.get("symbol"), "module_header")
        self.assertIn("import os", header_chunk.page_content)
        self.assertIn("GLOBAL_VAR", header_chunk.page_content)

        func_chunk = chunks[1]
        self.assertEqual(func_chunk.metadata.get("symbol"), "sample_func")
        self.assertIn("def sample_func", func_chunk.page_content)

    def test_prompt_builder_formatting_and_reasoning(self):
        doc = Document(
            page_content="def process_data(): return 42",
            metadata={
                "file": "app/services/processor.py",
                "symbol": "process_data",
                "start_line": 10,
                "end_line": 20,
            },
        )
        context_str = format_document_context([doc])
        self.assertIn("Source: app/services/processor.py", context_str)
        self.assertIn("Symbol: process_data", context_str)
        self.assertIn("Lines: 10-20", context_str)

        prompt = build_prompt("How is data processed?", [doc])
        self.assertIn("Archon AI", prompt)
        self.assertIn("app/services/processor.py", prompt)
        self.assertIn("USER QUESTION", prompt)

    def test_build_chat_provider_groq(self):
        from app.services.llm_service import build_chat_provider, GroqChatProvider
        provider = build_chat_provider(
            provider="groq",
            groq_api_key="gsk_test_123",
            groq_model="llama-3.3-70b-versatile"
        )
        self.assertIsInstance(provider, GroqChatProvider)
        self.assertEqual(provider._model, "llama-3.3-70b-versatile")

    def test_fallback_chat_provider_switches_on_failure(self):
        from app.services.llm_service import build_chat_provider, FallbackChatProvider, ChatCompletionProvider

        class FailingProvider(ChatCompletionProvider):
            def generate(self, prompt: str, max_retries: int = 3) -> str:
                raise RuntimeError("Primary provider overloaded")

        class WorkingProvider(ChatCompletionProvider):
            def generate(self, prompt: str, max_retries: int = 3) -> str:
                return "Response from fallback provider"

        fallback_provider = FallbackChatProvider(
            primary=FailingProvider(),
            fallback=WorkingProvider()
        )
        res = fallback_provider.generate("Test prompt")
        self.assertEqual(res, "Response from fallback provider")

        # Test build_chat_provider with 'fallback' option
        auto_provider = build_chat_provider(provider="fallback")
        self.assertIsInstance(auto_provider, FallbackChatProvider)


if __name__ == "__main__":
    unittest.main()
