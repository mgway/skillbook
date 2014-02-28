window.addEvent('domready', function() {
	if(window.location.hash) {
		split = window.location.hash.split('/');
		if(split[0] == '#character') {
			alert("showing character page");
		}
	}
	var clocks = [];
	skillbook.api('characters', function(characters) {
		var grid = $('pagegrid');
		characters.each(function(char) {
			grid.grab(character_row(char));
		});

		function character_row(char) {
			var row = new Element('div', {'class': 'uk-width-1-2', 'style':'padding-bottom: 10px'});
			var article = new Element('article', {'class': 'uk-comment'});
			var header = new Element('header', {'class': 'uk-comment-header'});
			var data = char['corporationname'] + "<br />" + skillbook.format_isk(char['balance']);
			if(char['training_end']) {
				var rowid = "timer_" + char['characterid'];
				data += "<br />Queue finishes in <span id='"+rowid+"'></span>";
				clocks += setInterval(function(){update_timer(rowid, char['training_end'])}, 200);
			}
			header.adopt(
				skillbook.portrait(char['characterid'], char['name'], 'Character', 128, 'uk-comment-avatar'), 
				new Element('h4', {'html': char['name'], 'class': 'uk-comment-title'}),
				new Element('div', {'html': data, 'class': 'uk-comment-meta'})
			);
			article.grab(header);
			row.grab(article);
			row.addEvent('click', function(e) {
				alert("TODO: showing skills for " + char['name']);
			});
			return row;
		}
	});

	function update_timer(id, endTime) {
		// This is rough, but we use moment and moment-precise to display the queue end time 
		// (provided by the api as a UTC timestamp) as months/days/hours/minutes
		element = $(id);
		var offset = new Date().getTimezoneOffset();
		var endTime = moment(endTime).subtract('minutes', offset);
		if(endTime - new Date().getTime() < 86400000) {
			element.setStyle('color', 'red');
		}
		element.title = endTime.format('LLLL');
		element.innerText = endTime.preciseDiff(moment())
	}
});

