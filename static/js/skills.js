window.addEvent('domready', function() {
	skillbook.cache = {}
	var clocks = [];
	var character = null;

	var rowtemplate = "<td colspan='2'><b>{name}</b><br />SP: {format_sp}/{format_next_sp} ({timeconstant}x)<div class='tooltip'>{tip}</div></td><td class='right'><img src='/static/img/skill{level}.png' /><br />Level {level}</td>";
	var tiptemplate = '<b>Completed Level:</b> {level}<br /><b>Training time:</b> {format_next_time}<br/><b>Attributes: </b> {training.primary}, {training.secondary} ({training.sp_hour} SP/Hour)<br /><br /><b>Description:</b><br />{description}';


	function Character(sheet) {
		var self = new Object();
		self.raw = sheet;
		self.charisma = sheet.charisma + sheet.charismabonus;
		self.intelligence = sheet.intelligence + sheet.intelligencebonus;
		self.memory = sheet.memory + sheet.memorybonus;
		self.perception = sheet.perception + sheet.perceptionbonus;
        self.willpower = sheet.willpower + sheet.willpowerbonus;
		self.estimated_sp = 0;
		self.sp = 0;

		self.draw = function() {
			var panel = new Element('div', {'class': 'uk-width-1-1 uk-hidden-small'});
			var list = new Element('dl', {'class': 'uk-description-list uk-description-list-horizontal'});
			var massaged = {'Bio': this.raw.bio, 'Balance': skillbook.format_isk(this.raw.balance),
				'Birthday': skillbook.to_localtime(this.raw.birthday).format('LLL'), 
				'Corporation': this.raw.corporationname, 'Skillpoints': 100, 
				'Clone': skillbook.format_number(this.raw.clonesp) + " (" + this.raw.clonegrade + ")"
			}

			_.each(massaged, function(value, key) {
				list.adopt(new Element('dt', {'html': key}), new Element('dd', {'html': value, 'id': 'sheet_'+key}));
			});
			panel.adopt(
				skillbook.portrait(sheet.characterid, sheet.name, 'Character', 128, 'uk-comment-avatar'), 
				list
			);
			return panel;
		}
		self.set_estimated_sp = function(estimated_sp) {
			self.estimated_sp = estimated_sp;
			$('sheet_Skillpoints').set('text', skillbook.format_number(self.sp+estimated_sp));
		}
		self.set_sp = function(sp) {
			self.sp = sp;
			$('sheet_Skillpoints').set('text', skillbook.format_number(sp));
			$('sheet_Skillpoints').set('title', 'Estimated. API Verified: '+skillbook.format_number(sp));
		}
		return self;
	};

	function Skill(attributes) {
		var self = new Object();
		_.each(attributes, function(val, key) {
			self[key] = val;
		});
		self.id = 'skill_' + self.typeid;
		self.raw = attributes;
		self.next_sp = skillbook.sp_next_level(self.level, self.timeconstant);
		self.format_sp = skillbook.format_number(self.skillpoints)
		self.format_next_sp = skillbook.format_number(self.next_sp);
		self.format_level = skillbook.roman(self.level);
		self.description = self.description.replace('\n', '<br />');
		self.training = skillbook.time_to_complete(character, self, self.level, self.skillpoints);
		self.format_next_time = skillbook.format_seconds(self.training.seconds);
		self.is_training = false;

		self.set_training = function(to_level){
			console.log($(this.id).getElements('img').get('href'));
		}
		self.draw_row = function() {
			this.tip = new Template().substitute(tiptemplate, this);
			return new Element('tr', {'html': new Template().substitute(rowtemplate, this), 'id': this.id});
		}
		return self;
	};

	if(window.location.hash) {
		split = window.location.hash.split('/');
		if(split[0] == '#character') {
			show_character(split[1]);
		} else {
			list_characters();	
		}
	} else {
		list_characters();
	}

	function clear() {
		$('pagegrid').empty();
		$$('table').dispose();
		clocks.each(function(idx) {clearInterval(idx)});
	}

	function list_characters() {

		window.location.hash = 'characters';
		$('pagetitle').set('text', 'Characters');

		skillbook.api('characters', function(characters) {
			var grid = $('pagegrid');
			characters.each(function(char) {
				grid.grab(character_row(char));
			});

			function character_row(char) {
				var row = new Element('div', {'class': 'uk-width-1-1 uk-width-medium-1-1 uk-width-large-1-2', 'style':'padding-bottom: 10px'});
				var article = new Element('article', {'class': 'uk-comment'});
				var header = new Element('header', {'class': 'uk-comment-header'});
				var data = char.corporationname + "<br />" + skillbook.format_isk(char.balance);
				if(char.training_end) {
					var rowid = "timer_" + char.characterid;
					data += "<br />Queue finishes in <span id='"+rowid+"'></span>";
					clocks.push(setInterval(function(){update_timer(rowid, char.training_end)}, 500));
				}
				header.adopt(
					skillbook.portrait(char.characterid, char.name, 'Character', 128, 'uk-comment-avatar'), 
					new Element('h4', {'html': char.name, 'class': 'uk-comment-title'}),
					new Element('div', {'html': data, 'class': 'uk-comment-meta'})
				);
				article.grab(header);
				row.grab(article);
				row.addEvent('click', function(e) {
					show_character(char.characterid);
				});
				return row;
			}

			function update_timer(id, endTime) {
				// This is rough, but we use moment and moment-precise to display the queue end time 
				// (provided by the api as a UTC timestamp) as months/days/hours/minutes
				element = $(id);
				var offset = new Date().getTimezoneOffset();
				var endTime = moment(endTime).subtract('minutes', offset);
				var delta = endTime - new Date().getTime();
				element.title = endTime.format('LLLL');
				element.innerText = endTime.preciseDiff(moment())
				if(delta < 86400000) {
					element.setStyle('color', 'red');
					if(delta < 0) {
						element.innerText = "0m";
					}
				}
			}
		});
	}

	function show_character(id) {
		// First, kill our timers
		clocks.each(function(idx) {clearInterval(idx)});

		// Push the character id onto the hash for bookmarking purposes (or something)
		window.location.hash = 'character/' + id;
		$('pagegrid').empty();

		// Check the cache first
		if(skillbook.cache[id] == undefined) {
			// Fetch the list of skills (static)
				skillbook.cache[id] = {}

			skillbook.api("sheet/" + id, function(sheet) {
				skillbook.cache[id].sheet = new Character(sheet);
				display_sheet();

				skillbook.api("skills/" + id, function(skills) {
					skillbook.cache[id].skills = [];
					skills.each(function(skill) {
						skillbook.cache[id].skills.push(new Skill(skill));
					});
					display_skills();
				});

				skillbook.api("queue/" + id, function(queue) {
					skillbook.cache[id].queue = queue;
					display_queue();
				});
			});
		} else {
			display_sheet();
			display_skills();
			display_queue();
		}
		clocks.push(setInterval(function(){display_queue()}, 5000));

		function display_sheet() {
			character = skillbook.cache[id].sheet;

			// Set up our header
			var list_chars = new Element('a', {'text': 'Characters', 'style': 'cursor: pointer', 'class': 'uk-link-muted'});
			var trailer = new Element('span', {'html': ' &raquo; ' + character.raw.name});
			list_chars.addEvent('click', list_characters);
			$('pagetitle').empty().adopt(list_chars, trailer);

			// And draw the character panel
			$('pagegrid').grab(character.draw());
		}

		function display_skills() {
			total_sp = 0;
			var groups = _.groupBy(skillbook.cache[id].skills, function(skill){ return skill.groupname });
			var frame = $('frame');
			_.sortBy(groups, function(group) { return group[0].groupname }).each(function(skills, key) { 
				frame.grab(skill_category(skills, key));
			});

			character.set_sp(total_sp);
		}

		function display_queue() {
			var queue = skillbook.cache[id].queue;
			var panel = $('skillqueue');
			if (panel == undefined) {
				panel = new Element('div', {'class': 'uk-width-1-1 uk-panel', 'id':'skillqueue', 'style': 'padding-top: 10px'});
			} else {
				panel.empty();
			}

			// Bail if the queue is empty
			if (queue.length == 0)
				return;

			var table = new Element('table', {'style': 'width: 100%', 'id': 'queue'});
			var row = new Element('tr');

			estimated_sp = 0;

			var current_skill; 
			queue.each(function(skill) {
				var start = skillbook.to_localtime(skill.starttime);
				var end = skillbook.to_localtime(skill.endtime);
				var now = moment();
				var skillpercent;
				var tip = '<b>{name} {level}<br />Starts:</b> {start}<br/><b>Finishes:</b> {end}';

				estimated_sp += skillbook.estimate_sp(skill.startsp, skill.endsp, skill.starttime, skill.endtime);

				if(start < now && end > now) {
					// Skill is being trained now
					skillpercent = Math.min(end - now, 86400000) / 864000;
					current_skill = skill;
					tip = '<b>{name} {level}<br />Finishes:</b> {end}';
				} else if (start > now) {
					// Skill fits in 24 hour window, but isn't being trained now
					skillpercent = Math.min(end-start, 86400000) / 864000;
				} else {
					return; // Skill training completed
				}
				var td = new Element('td', {'style':'width: '+skillpercent+'%;', 'html':'&nbsp;'});
				var data = {'name': skill.name, 'level': skillbook.roman(skill.level), 'start': start.format('LLLL'), 'end': end.format('LLLL')};
				td.grab(new Element('span', {'class': 'tooltip', 'html': new Template().substitute(tip, data)}));
				row.adopt(td);
			});
			
			var endTime = skillbook.to_localtime(queue.getLast().endtime);
			if (endTime - moment() < 86400000) {
				var empty = new Element('td', {'class': 'error', 'style': 'background-color: #842107', 'html': '&nbsp'});
				empty.grab(new Element('span', {'class': 'tooltip', 'html': "Free Room <br>" + moment(endTime).preciseDiff(moment().add('hours', 24))}));
				row.adopt(empty);
			} else {
				panel.adopt(new Element('span', {'class': 'uk-float-left', 'text': endTime.preciseDiff(moment())}));
				panel.adopt(new Element('span', {'class': 'uk-float-right', 'text': endTime.format('LLLL')}));
			}

			var grid = $('pagegrid');
			var template = "<tr><td>Currently Training:</td><td><strong>{name}</strong> {level}</td></tr><tr><td></td><td>{end}</td></tr><tr><td></td><td>{delta}</td></tr>";
			table.adopt(row);
			panel.adopt(table);
			var end = skillbook.to_localtime(current_skill.endtime); 
			var data = {'name': current_skill.name, 'end': end.format('LLLL'), 'delta': end.preciseDiff(moment()), 
				'level': skillbook.roman(current_skill.level)}
			panel.grab(new Element('table', {'html': new Template().substitute(template, data), 'id': 'current_train'}));
			grid.grab(panel);
			character.set_estimated_sp(estimated_sp);
		}

		function skill_category(skills, header) {
			var headertemplate = "<tr style='cursor: pointer'><th style='width: 40%'>{h}</th><th style='width: 40%'><small>{count} skills &mdash; {sp} points</small></th><th>&nbsp;</th></tr>";
			var table = new Element('table', {'class': 'uk-table uk-table-striped uk-table-condensed skills', 'style':'padding-bottom: 10px'});
			var tbody = new Element('tbody');
			var category_sp = 0;

			_.sortBy(skills, function(skill) { return skill.name }).each(function(skill) {
				tbody.grab(skill.draw_row());
				category_sp += skill.skillpoints;
			});

			total_sp += category_sp;

			var data = {'h': skills[0].groupname, 'sp': skillbook.format_number(category_sp), 'count': skills.length};
			var thead = new Element('thead', {'html': new Template().substitute(headertemplate, data)});
			thead.addEvent('click', function(e) {
				tbody.toggle();
			});

			table.adopt(thead, tbody)
			return table;
		}
	}
});

