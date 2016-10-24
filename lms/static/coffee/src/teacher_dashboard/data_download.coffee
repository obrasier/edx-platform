###
Data Download Section

imports from other modules.
wrap in (-> ... apply) to defer evaluation
such that the value can be defined later than this assignment (file load order).
###

# Load utilities
std_ajax_err = -> window.InstructorDashboard.util.std_ajax_err.apply this, arguments
PendingInstructorTasks = -> window.InstructorDashboard.util.PendingInstructorTasks
ReportDownloads = -> window.InstructorDashboard.util.ReportDownloads

# Data Download Section
class DataDownload
  constructor: (@$section) ->
    # attach self to html so that instructor_dashboard.coffee can find
    #  this object to call event handlers like 'onClickTitle'
    @$section.data 'wrapper', @

    @$calculate_grades_csv_btn = @$section.find("input[name='calculate-grades-csv']'")
    @$problem_grade_report_csv_btn = @$section.find("input[name='problem-grade-report']'")
    @$download_class_submissions_btn = @$section.find("input[name='download-class-submissions']'")
    
    # point to class_code selector
    @$class_code                      = @$section.find '.wrapper-member-select'
    @$class_code_select               = @$class_code.find '.member-lists-selector'
    @$arrange_by_select               = @$section.find("input[name='download-class-submissions-arrange_by']")
    
    # response areas
    @$download                        = @$section.find '.data-download-container'
    @$download_display_text           = @$download.find '.data-display-text'
    @$download_request_response_error = @$download.find '.request-response-error'
    @$reports                         = @$section.find '.reports-download-container'
    @$download_display_table          = @$reports.find '.profile-data-display-table'
    @$reports_request_response        = @$reports.find '.request-response'
    @$reports_request_response_error  = @$reports.find '.request-response-error'
    @$download_submissions_response   = @$section.find '.download-submissions-response'

    @report_downloads = new (ReportDownloads()) @$section
    @instructor_tasks = new (PendingInstructorTasks()) @$section
    @clear_display()

    @$class_code_select.change (e) =>
      @report_downloads.reload_report_downloads()

    @$calculate_grades_csv_btn.click (e) =>
      @onClickGradeDownload @$calculate_grades_csv_btn, gettext("Error generating grades. Please try again.")

    @$problem_grade_report_csv_btn.click (e) =>
      @onClickGradeDownload @$problem_grade_report_csv_btn, gettext("Error generating problem grade report. Please try again.")

     @$download_class_submissions_btn.click (e) =>
      @onClickDownloadSubs @$download_class_submissions_btn, gettext("Error generating download link. Please try again.")

  onClickGradeDownload: (button, errorMessage) ->
      # Clear any CSS styling from the request-response areas
      #$(".msg-confirm").css({"display":"none"})
      #$(".msg-error").css({"display":"none"})
      @clear_display()
      url = button.data 'endpoint'
      $.ajax
        type: 'GET'
        dataType: 'json'
        url: url
        data: {class_code: @$class_code_select.val(),arrange_by: @$arrange_by_select.val()}
        error: (std_ajax_err) =>
          @$reports_request_response_error.text errorMessage
          $(".msg-error").css({"display":"block"})
        success: (data) =>
          @$reports_request_response.text data['status']
          $(".msg-confirm").css({"display":"block"})

  onClickDownloadSubs: (button, errorMessage) ->
      # Clear any CSS styling from the request-response areas
      #$(".msg-confirm").css({"display":"none"})
      #$(".msg-error").css({"display":"none"})
      @clear_display()
      url = button.data 'endpoint'
      $.ajax
        type: 'GET'
        dataType: 'json'
        url: url
        data: {class_code: @$class_code_select.val(),arrange_by: @$arrange_by_select.val()}
        error: (std_ajax_err) =>
          @$reports_request_response_error.text errorMessage
          $(".msg-error").css({"display":"block"})
        success: (data) =>
          if data.success
            @$download_submissions_response.text data['msg']
            window.open(data['url'])
          else 
            @$download_submissions_response.text data['msg']


  # handler for when the section title is clicked.
  onClickTitle: ->
    # Clear display of anything that was here before
    @clear_display()
    @instructor_tasks.task_poller.start()
    @report_downloads.downloads_poller.start()

  # handler for when the section is closed
  onExit: ->
    @instructor_tasks.task_poller.stop()
    @report_downloads.downloads_poller.stop()

  clear_display: ->
    # Clear any generated tables, warning messages, etc.
    @$download_display_text.empty()
    @$download_display_table.empty()
    @$download_request_response_error.empty()
    @$reports_request_response.empty()
    @$reports_request_response_error.empty()
    @$download_submissions_response.empty()
    # Clear any CSS styling from the request-response areas
    $(".msg-confirm").css({"display":"none"})
    $(".msg-error").css({"display":"none"})

# export for use
# create parent namespaces if they do not already exist.
_.defaults window, InstructorDashboard: {}
_.defaults window.InstructorDashboard, sections: {}
_.defaults window.InstructorDashboard.sections,
  DataDownload: DataDownload
