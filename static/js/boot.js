requirejs.config({
  baseUrl: '/static/js',
  paths: {
    bower: '/bower_components',
    flight: '/bower_components/flight/lib',
    depot: '/bower_components/depot/depot',
    jquery: '/bower_components/jquery/dist/jquery',
    moment: '/bower_components/moment/moment',
    hbs: '/bower_components/require-handlebars-plugin/hbs',
    underscore: '/bower_components/underscore/underscore',
    schedule: '/bower_components/flight-schedule/lib/schedule',
    flight_router: '/bower_components/flight-router/lib/with_route'
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
    'flight/debug'
  ],

  function(debug) {
    debug.enable(true);
    require(['page/skills'], function(initialize) {
        initialize();
    });
  }
);
