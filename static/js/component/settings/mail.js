define(
    [
        'flight/lib/component',
        'common/ajax',
        'common/mailgun_validator'
    ],
    function(defineComponent, ajax, mailgun_validate) {
        return defineComponent(mail, ajax);
        
        function mail () {
            
            var timeout;
            this.defaultAttrs({
                mailSelector: 'input[name=email]',
                apiKey: 'pubkey-39bb1e3db1bd1ba1f6658e50f354d67f',
                confirmSelector: '#confirmation'
            });
            
            this.validateMail = function(e, data) {
                clearTimeout(timeout);
                var key = this.attr.apiKey;
                timeout = setTimeout(function(){
                    mailgun_validate($(e.target).val(), {
                        api_key: key,
                        success: function(response) {
                            var el = $('#mail-validation');
                            if(response.is_valid) {
                                el.text('That address looks good!');
                                el.removeClass('uk-alert-danger').addClass('uk-alert-success');
                            } else {
                                if(response.did_you_mean) {
                                    el.text('Did you mean: ' + response.did_you_mean + ' ?');
                                } else {
                                    el.text('Are you sure about that address?');
                                }
                                el.removeClass('uk-alert-success').addClass('uk-alert-danger');
                            }
                            el.show();
                        }
                    });
                }, 250);
            };
			
			this.confirmMail = function(e, data) {
                if($(e.target).data('sent')) {
                    return;
                }
                
                this.post({
                    xhr: {
                        url: '/mail/confirm',
                    },
                    events: {
                        done: 'apiConfirmResponse',
                    },
                    meta: {
                        key: 'data',
                    }
                });
                
                this.data('sent', true)
			};
			
			this.mailConfirmationSent = function(e, data) {
			    $(this.attr.confirmSelector).html('<i class="fa fa-envelope"></i> mail sent');
			};
			
            this.after('initialize', function() {
                this.on('apiConfirmResponse', this.mailConfirmationSent);
                this.on('keyup', { 'mailSelector': this.validateMail });
                this.on('keyup', { 'confirmSelector': this.confirmMail });
            });
       }
   }
);