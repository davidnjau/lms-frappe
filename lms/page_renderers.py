"""Custom page renderers for LMS app.

Handles rendering of profile pages.
"""

import mimetypes
import os
from urllib.parse import unquote

import frappe
from frappe.website.page_renderers.base_renderer import BaseRenderer
from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file


class _ExtractedPackageRenderer(BaseRenderer):
	"""Shared serving logic for extracted zip content packages (SCORM, H5P, ...)
	stored at <site>/private|public/<PACKAGE_ROOT>/<course>/<title>/... —
	see SCORMRenderer/H5PRenderer below, which only set the two class attrs.
	"""

	PACKAGE_ROOT = None
	CHAPTER_FLAG_FIELD = None

	def can_render(self):
		return f"{self.PACKAGE_ROOT}/" in self.path

	# Disk roots tried, in order, to resolve package bytes. New packages are extracted
	# under private/<root> (gated: /private is always routed through Frappe, so this
	# permission gate runs in production too). Legacy packages already extracted under
	# public/<root> are still served as a fallback — but the standard bench nginx config
	# serves public/ directly (try_files .../public/$uri @webserver), so for those legacy
	# files this Python gate is BYPASSED in production, exactly as before. Such packages
	# stay ungated in prod until re-uploaded (re-extraction lands them in private). New
	# uploads are gated in dev and prod alike.
	_DISK_ROOTS = ("private", "public")

	def _check_permission(self):
		from lms.lms.permissions import can_access_lesson

		parts = self.path.strip("/").split("/")
		# <root>/<course>/<title>/...
		if len(parts) < 3 or parts[0] != self.PACKAGE_ROOT:
			raise frappe.PermissionError
		course, title = unquote(parts[1]), unquote(parts[2])

		chapter = frappe.db.get_value(
			"Course Chapter",
			{"course": course, "title": title, self.CHAPTER_FLAG_FIELD: 1},
			"name",
		)
		if not chapter:
			raise frappe.PermissionError

		# Package chapters are created with exactly one lesson (upsert_chapter invariant
		# in api.py). order_by keeps the access check deterministic if that ever changes.
		lesson = frappe.db.get_value("Lesson Reference", {"parent": chapter}, "lesson", order_by="idx asc")
		if not lesson or not can_access_lesson(lesson):
			frappe.logger("lms.security").warning(
				"%s resource access denied: user=%s path=%s",
				self.PACKAGE_ROOT,
				frappe.session.user,
				self.path,
			)
			raise frappe.PermissionError

	def _is_safe_path(self, path):
		resolved = os.path.realpath(path)
		for base in self._DISK_ROOTS:
			package_root = os.path.realpath(os.path.join(frappe.local.site_path, base, self.PACKAGE_ROOT))
			if resolved == package_root or resolved.startswith(package_root + os.sep):
				return True
		return False

	def _serve_file(self, path):
		f = open(path, "rb")
		response = Response(wrap_file(frappe.local.request.environ, f), direct_passthrough=True)
		response.mimetype = mimetypes.guess_type(path)[0]
		return response

	def render(self):
		self._check_permission()
		# Try private/<root> first (new, gated), then public/<root> (legacy).
		for base in self._DISK_ROOTS:
			response = self._render_from_root(base)
			if response is not None:
				return response

	def _render_from_root(self, base):
		path = os.path.join(frappe.local.site_path, base, self.path.lstrip("/"))

		if not self._is_safe_path(path):
			raise frappe.PermissionError

		extension = os.path.splitext(path)[1]
		if not extension:
			path = f"{path}.html"

		# check if path exists and is actually a file and not a folder
		if os.path.exists(path) and os.path.isfile(path):
			return self._serve_file(path)
		else:
			path = path.replace(".html", "")
			if os.path.exists(path) and os.path.isdir(path):
				index_path = os.path.join(path, "index.html")
				if os.path.exists(index_path):
					return self._serve_file(index_path)
			elif not os.path.exists(path):
				chapter_folder = "/".join(self.path.split("/")[:3])
				chapter_folder_path = os.path.realpath(frappe.get_site_path(base, chapter_folder))
				file = path.split("/")[-1]
				correct_file_path = None

				if not self._is_safe_path(chapter_folder_path):
					raise frappe.PermissionError

				for root, _dirs, files in os.walk(chapter_folder_path):
					if file in files:
						correct_file_path = os.path.join(root, file)
						break

				if correct_file_path and self._is_safe_path(correct_file_path):
					return self._serve_file(correct_file_path)
		return None


class SCORMRenderer(_ExtractedPackageRenderer):
	PACKAGE_ROOT = "scorm"
	CHAPTER_FLAG_FIELD = "is_scorm_package"


class H5PRenderer(_ExtractedPackageRenderer):
	PACKAGE_ROOT = "h5p"
	CHAPTER_FLAG_FIELD = "is_h5p_package"
