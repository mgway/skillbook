define(
    [
        'flight/lib/component',
        'hbs!templates/character/alerts',
        'hbs/handlebars'
    ],
    function(defineComponent, template, handlebars) {
        return defineComponent(characterAlert);
        
        function characterAlert () {
            
            this.defaultAttrs({
                numberSelector: 'input[type=number]',
                saveSelector: '#alert-save'
            });
            
            this.render = function(e, data) {
                data.data.updated = data.meta.updated;
                this.$node.html(template(data.data));
            };
            
            this.switchTab = function(e, data) {
                if (data.page == 'alerts') {
                    this.trigger(document, 'uiNeedsAlertList', {id: data.id});
                    this.characterId = data.id;
                }
            };
            
            this.validate = function(e, data) {
                var el = $(e.target);
                var value = parseInt(el.val(), 10);
                el.removeClass('uk-form-danger').removeClass('uk-form-success');
                
                if(isNaN(value)) {
                    el.val(el.data('default'));
                    el.addClass('uk-form-danger');
                }
                else if(value > el.attr('max')) {
                    el.val(el.attr('max'));
                    el.addClass('uk-form-danger');
                }
                else if(value < el.attr('min')) {
                    el.val(el.attr('min'));
                    el.addClass('uk-form-danger');
                } else {
                    el.addClass('uk-form-success');
                }
            };
            
            this.saveAlerts = function(e) {
                var data = [];
                var rows = this.$node.find('tbody tr');
                rows.each(function(idx, el) {
                    el = $(el);
                    var row = {
                        'option_1_value': el.find('input[type=number]').val(),
                        'alert_type_id': el.data('type'),
                        'enabled': el.find('input[type=checkbox]').prop('checked')
                    };
                    data.push(row);
                });
                this.trigger(document, 'uiSaveAlertList', {alerts: data, id: this.characterId});
            };
           
            this.after('initialize', function() {
                this.on(document, 'dataCharacterAlertListResponse', this.render);
                this.on(document, 'uiSwitchCharacterTab', this.switchTab);
                
                this.on('focusout', { 'numberSelector': this.validate });
                this.on('click', { 'saveSelector': this.saveAlerts });
            });
       }
   }
);