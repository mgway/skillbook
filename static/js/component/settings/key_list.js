define(
    [
        'flight/lib/component',
        'common/ajax',
        'hbs!templates/settings/key_list'
    ],
    function(defineComponent, ajax, template) {
        return defineComponent(keyList, ajax);
        
        function keyList () {
            
            this.defaultAttrs({
                deleteSelector: '.uk-icon-trash-o',
                formSelector: '#character-add-form'
            });
            
            this.render = function(e, data) {
                this.$node.html(template(data));
            };
            
            this.deleteKey = function(e, data) {
                if(!confirm('Are you sure you want to delete this key?'))
                    return;
                var id = $(data.el).data('keyid');
                $.ajax({
                    type: 'DELETE',
                    url: '/api/key/' + id,
                    success: function() {
                    	$('#key_'+id).slideUp();
                    	localStorage.removeItem('characters');
                    }
        		});
            };
            
            function getCookie(name) {
                var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
                return r ? r[1] : undefined;
            }
            
            this.addKey = function(e, data) {
                e.preventDefault();
                var xhr_data = JSON.stringify({
                    'keyid': $('#keyid').val(), 
                    'vcode': $('#vcode').val()
                });
                
                this.post({
                    xhr: {
                        url: '/api/key/',
                        data: xhr_data, 
                    },
                    events: {
                        done: 'apiKeysResponse',
                        fail: 'apiKeysResponseFailed'
                    },
                    meta: {
                        key: 'keys',
                    }
                });
                
                localStorage.removeItem('characters');
            };
            
            this.addKeyFailed = function(e, data) {
                $('#character-add-form-error').text(data.keys.error);
            };
            
            this.getKeys = function(e, data) {
                this.get({
                    xhr: {
                        url: '/api/key/'
                    },
                    events: {
                        done: 'apiKeysResponse'
                    },
                    meta: {
                        key: 'keys',
                    }
                });
            };
           
            this.after('initialize', function() {
                this.on('apiKeysResponse', this.render);
                this.on('uiKeysRequest', this.getKeys);
                this.on('apiKeysResponseFailed', this.addKeyFailed);
                
                this.on('click', { 'deleteSelector': this.deleteKey });
                this.on('submit', { 'formSelector': this.addKey });
                
                this.trigger('uiKeysRequest');
            });
       }
   }
);