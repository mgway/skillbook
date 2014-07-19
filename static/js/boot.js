requirejs.config({
  baseUrl: '/static/js',
  paths: {
    bower: 'bower_components',
    flight: 'bower_components/flight',
    jquery: 'bower_components/jquery/dist/jquery',
    moment: 'bower_components/moment/moment',
    hbs: 'bower_components/require-handlebars-plugin/hbs',
    underscore: 'bower_components/underscore/underscore',
    schedule: 'bower_components/flight-schedule/lib/schedule',
    history: 'bower_components/flight-history/lib/flight-history',
  },
  hbs: {
        helpers: true,
        i18n: false,
        templateExtension: 'hbs',
        partialsUrl: 'templates/partials'
    }
});

require(
  [
    'flight/lib/debug'
  ],

  function(debug) {
    debug.enable(true);
    require(['page/skills'], function(initialize) {
        initialize();
    });
  }
);
