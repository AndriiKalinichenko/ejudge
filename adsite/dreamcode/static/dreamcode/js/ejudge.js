if (typeof DOJ == 'undefined') { // DOJ = django onlinejudge
  DOJ = {};
}


DOJ = function () {
    var getResults = function (url, res_el) {
        $.ajax({
            url: url,
            type: "GET",
            success: function(data) {
                $(res_el).html(data);
                $('[data-toggle="popover"]').popover();
            }
        });
    }

    var prepareDiff = function (slug) {
        var byId = function (id) { return document.getElementById(id); },
          base = difflib.stringAsLines(byId(slug+"-template").textContent),
          newtxt = difflib.stringAsLines(byId(slug+"-code").textContent),
          sm = new difflib.SequenceMatcher(base, newtxt),
          opcodes = sm.get_opcodes(),
          diffoutputdiv = byId(slug+"-diff");
          //contextSize = byId("contextSize").textContent;

        diffoutputdiv.innerHTML = "";
        //contextSize = contextSize || null;

        diffoutputdiv.appendChild(diffview.buildView({
          baseTextLines: base,
          newTextLines: newtxt,
          opcodes: opcodes,
          //opcodes: data.opcodes,
          baseTextName: "",
          newTextName: "",
          contextSize: 1,
          viewType: 1 // 0 or 1
        }))
    }


    var submissionFormSelector = 'form#submission';
    var _submissionResultsSelector = 'div#subres';

    function resetSubmission(e) {
        $.ajax({
          url: e.data.url,
          type: "GET",
          success: function(data) {
            var editor = ace.edit($(submissionFormSelector+" .django-ace-widget .ace_editor")[0]);
            //var code = editor.getSession().getValue();
            editor.getSession().setValue(data['template']);
          }
        });
    }

    function pollResults(timeout, url) {
       setTimeout(function(){
          $.ajax({
            url: url,
            type: "GET",
            success: function(data) {
              $(_submissionResultsSelector).html(data);
              // check if data need polling result pending
              $('[data-toggle="popover"]').popover();
              if(!!($('<html />').html(data).find('#result.pd').length))
                pollResults(1000, url);
            }
          });
      }, timeout);
    }

    function submissionSubmit(e) {
      e.preventDefault();
      $.ajax({
        url: e.data.url,
        type: "POST",
        data: $(submissionFormSelector).serialize(),
        success: function(data) {
          if (data['submission_status']=="CE") {
            // show compile errors
            var ce = "";
            if (data['compile_err'])
              ce += '<pre class="error">'+data['compile_err']+'</pre>';
            if (data['compile_out'])
              ce += '<pre class="output">'+data['compile_out']+'</pre>';
            $(_submissionResultsSelector).html(ce);
          }
          else {
            pollResults(0, e.data.resultsUrl);
          }
        },
        error: function () {
          //TODO:
          $(submissionFormSelector).find('.error-message').show();
        }
      });
    };



    return  {
        getResults: getResults,
        prepareDiff: prepareDiff,
        submissionFormSelector: submissionFormSelector,
        resetSubmission: resetSubmission,
        pollResults: pollResults,
        submissionSubmit: submissionSubmit
    }
}();
