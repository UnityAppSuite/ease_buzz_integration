from . import __version__ as app_version

app_name = "easebuzz"
app_title = "Easebuzz"
app_publisher = "Hybrowlabs"
app_description = "EaseBuzz Integration"
app_email = "easebuzz@hybrowlabs.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/easebuzz/css/easebuzz.css"
# app_include_js = "/assets/easebuzz/js/easebuzz.js"

# include js, css files in header of web template
# web_include_css = "/assets/easebuzz/css/easebuzz.css"
# web_include_js = "/assets/easebuzz/js/easebuzz.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "easebuzz/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "easebuzz.utils.jinja_methods",
#	"filters": "easebuzz.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "easebuzz.install.before_install"
# after_install = "easebuzz.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "easebuzz.uninstall.before_uninstall"
# after_uninstall = "easebuzz.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "easebuzz.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Web Form": "easebuzz.overrides.payment_webform.CustomPaymentWebForm"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Easebuzz Settlement Log": {
		"before_save": "easebuzz.easebuzz.doctype.easebuzz_settlement_log.easebuzz_settlement_log.process_log"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"easebuzz.tasks.all"
#	],
#	"daily": [
#		"easebuzz.tasks.daily"
#	],
#	"hourly": [
#		"easebuzz.tasks.hourly"
#	],
#	"weekly": [
#		"easebuzz.tasks.weekly"
#	],
#	"monthly": [
#		"easebuzz.tasks.monthly"
#	],
# }

# Testing
# -------

# before_tests = "easebuzz.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "easebuzz.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "easebuzz.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["easebuzz.utils.before_request"]
# after_request = ["easebuzz.utils.after_request"]

# Job Events
# ----------
# before_job = ["easebuzz.utils.before_job"]
# after_job = ["easebuzz.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"easebuzz.auth.validate"
# ]
