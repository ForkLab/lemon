dashboard.views.AdminLog = dashboard.views.Template.extend({

  tagName: "div",
  className: "dashboard-admin-log-instance",
  templateId: "dashboard/js/templates/admin_log",

  initialize: function() {
    dashboard.views.Template.prototype.initialize.call(this);
    if (dashboard.collections.adminLogEntries.length !== 0) {
      this.render();
    }
    dashboard.collections.adminLogEntries.bind("reset", this.render);
  },

  render: function() {
    dashboard.views.Template.prototype.render.call(this);
    this.$("tr:last").addClass("last");
    return this;
  },

  templateContext: function() {
    return {entries: dashboard.collections.adminLogEntries.toJSON()};
  }

});
