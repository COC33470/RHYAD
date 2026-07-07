import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engine.utils.pdf import PDFConversionError, convert_docx_to_pdf, find_libreoffice_executable


class PDFConversionTest(unittest.TestCase):
    def test_find_libreoffice_executable_accepts_macos_app_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            soffice_path = Path(tmp) / "LibreOffice.app" / "Contents" / "MacOS" / "soffice"
            soffice_path.parent.mkdir(parents=True)
            soffice_path.write_text("", encoding="utf-8")

            with patch("engine.utils.pdf.which", return_value=None):
                with patch("engine.utils.pdf.MACOS_LIBREOFFICE_PATHS", (soffice_path,)):
                    self.assertEqual(find_libreoffice_executable(), str(soffice_path))

    def test_missing_libreoffice_reports_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "sample.docx"
            docx_path.write_bytes(b"docx")

            with patch("engine.utils.pdf.which", return_value=None):
                with patch("engine.utils.pdf.MACOS_LIBREOFFICE_PATHS", ()):
                    with self.assertRaisesRegex(PDFConversionError, "LibreOffice executable not found"):
                        convert_docx_to_pdf(docx_path, Path(tmp) / "pdf")

    def test_successful_conversion_returns_expected_pdf_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docx_path = root / "sample.docx"
            pdf_dir = root / "pdf"
            docx_path.write_bytes(b"docx")

            def fake_run(cmd, check, text, stdout, stderr):
                self.assertIn("pdf:writer_pdf_Export", cmd)
                self.assertTrue(any(arg.startswith("-env:UserInstallation=file://") for arg in cmd))
                pdf_dir.mkdir(parents=True, exist_ok=True)
                (pdf_dir / "sample.pdf").write_bytes(b"%PDF-1.7")
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

            with patch("engine.utils.pdf.which", return_value="/usr/bin/soffice"):
                with patch("engine.utils.pdf.subprocess.run", side_effect=fake_run):
                    pdf_path = convert_docx_to_pdf(docx_path, pdf_dir)

            self.assertEqual(pdf_path, pdf_dir / "sample.pdf")
            self.assertTrue(pdf_path.exists())

    def test_failed_libreoffice_raises_without_fallback_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docx_path = root / "sample.docx"
            pdf_dir = root / "pdf"
            docx_path.write_bytes(b"docx")

            def fake_run(cmd, check, text, stdout, stderr):
                return subprocess.CompletedProcess(cmd, 134, stdout="", stderr="Abort trap: 6")

            with patch("engine.utils.pdf.which", return_value="/usr/bin/soffice"):
                with patch("engine.utils.pdf.subprocess.run", side_effect=fake_run):
                    with self.assertRaises(PDFConversionError) as context:
                        convert_docx_to_pdf(docx_path, pdf_dir)

            self.assertIn("LibreOffice PDF conversion failed with exit code 134", str(context.exception))
            self.assertIn("Abort trap: 6", str(context.exception))
            self.assertFalse((pdf_dir / "sample.pdf").exists())


if __name__ == "__main__":
    unittest.main()
