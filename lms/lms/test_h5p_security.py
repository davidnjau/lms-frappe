# Copyright (c) 2026, Frappe and Contributors
# See license.txt

"""H5P security regression tests, mirroring test_scorm_security.py: the H5P
renderer/extraction path reuses the same generic _content_package_extract_path/
extract_content_package helpers SCORM was refactored onto (see api.py), so these
confirm the shared containment logic holds for package_type="h5p" too."""

import os
import shutil
import tempfile
import unittest
import zipfile

import frappe

from lms.lms.api import _content_package_extract_path, extract_content_package
from lms.page_renderers import H5PRenderer


class TestH5PExtractPath(unittest.TestCase):
	"""A traversal chapter title must not resolve outside the course's own dir."""

	def test_normal_title_stays_in_course_dir(self):
		course_root = os.path.realpath(frappe.get_site_path("private", "h5p", "my-course"))
		path = _content_package_extract_path("h5p", "my-course", "chapter-1")
		self.assertEqual(path, os.path.join(course_root, "chapter-1"))

	def test_parent_traversal_in_title_is_rejected(self):
		with self.assertRaises(frappe.exceptions.ValidationError):
			_content_package_extract_path("h5p", "my-course", "../victim-course/victim-chapter")

	def test_absolute_title_is_rejected(self):
		with self.assertRaises(frappe.exceptions.ValidationError):
			_content_package_extract_path("h5p", "my-course", "/srv/other/x")

	def test_empty_course_is_rejected(self):
		with self.assertRaises(frappe.exceptions.ValidationError):
			_content_package_extract_path("h5p", "", "victim-course/chapter-1")

	def test_dot_title_is_rejected(self):
		with self.assertRaises(frappe.exceptions.ValidationError):
			_content_package_extract_path("h5p", "my-course", ".")


class TestH5PExtractContainment(unittest.TestCase):
	"""extract_content_package() must never write outside the package's own course dir."""

	COURSE_A = "ct-h5p-course-a"
	COURSE_B = "ct-h5p-course-b"

	def setUp(self):
		self.h5p_root = os.path.realpath(frappe.get_site_path("private", "h5p"))
		self._tmp = tempfile.mkdtemp()
		self.zip_path = os.path.join(self._tmp, "pkg.h5p")
		self._make_zip([("h5p.json", '{"title": "Test"}'), ("content/content.json", "{}")])

		self._orig_get_doc = frappe.get_doc

		def fake_get_doc(doctype, *args, **kwargs):
			if doctype == "File":
				return frappe._dict(get_full_path=lambda: self.zip_path)
			return self._orig_get_doc(doctype, *args, **kwargs)

		frappe.get_doc = fake_get_doc

	def tearDown(self):
		frappe.get_doc = self._orig_get_doc
		shutil.rmtree(self._tmp, ignore_errors=True)
		for course in (self.COURSE_A, self.COURSE_B):
			shutil.rmtree(os.path.join(self.h5p_root, course), ignore_errors=True)

	def _make_zip(self, entries):
		with zipfile.ZipFile(self.zip_path, "w") as zf:
			for name, content in entries:
				zf.writestr(name, content)

	def _extract(self, course, title):
		return extract_content_package("h5p", course, title, frappe._dict(name="dummy"))

	def test_benign_title_extracts_inside_course_dir(self):
		path = self._extract(self.COURSE_A, "chapter-1")
		course_root = os.path.join(self.h5p_root, self.COURSE_A)
		self.assertTrue(os.path.realpath(path).startswith(course_root + os.sep))
		self.assertTrue(os.path.isfile(os.path.join(path, "h5p.json")))

	def test_traversal_title_cannot_overwrite_another_course(self):
		victim_dir = os.path.join(self.h5p_root, self.COURSE_B, "victim-chapter")
		with self.assertRaises(frappe.exceptions.ValidationError):
			self._extract(self.COURSE_A, f"../{self.COURSE_B}/victim-chapter")
		self.assertFalse(os.path.exists(victim_dir), "traversal title wrote into another course")


class TestH5PRendererSafePath(unittest.TestCase):
	def setUp(self):
		self.h5p_root = os.path.realpath(frappe.get_site_path("private", "h5p"))

	def _renderer(self, path="/h5p/c/t/index.html"):
		r = H5PRenderer.__new__(H5PRenderer)
		r.path = path
		return r

	def test_path_inside_h5p_root_is_allowed(self):
		inside = os.path.join(self.h5p_root, "c", "t", "index.html")
		self.assertTrue(self._renderer()._is_safe_path(inside))

	def test_parent_traversal_is_rejected(self):
		escape = os.path.join(self.h5p_root, "c", "t", "..", "..", "..", "..", "etc", "passwd")
		self.assertFalse(self._renderer()._is_safe_path(escape))

	def test_can_render_only_matches_h5p_paths(self):
		self.assertTrue(self._renderer("/h5p/c/t/index.html").can_render())
		self.assertFalse(self._renderer("/scorm/c/t/index.html").can_render())
