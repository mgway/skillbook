(function() {
	Object.append(window.skillbook, {
		'api': function(path, cb) {
			new Request.JSON({
				'url': '/api/' + path,
				'onSuccess': cb,
				'onFailure': function(xhr) {
					alert("API GET failure: " + xhr);
				},
				'onComplete': function() {
					var loading = $('loading');
					if (loading)
						loading.setStyle('display', 'none');
					},
			}).get();
		},
		'portrait': function(id, text, img_dir, size, cls) {
			var extension = 'png';
			if (img_dir == 'Character')
				extension = 'jpg';
			var img = new Element('img', {
				'src': 'https://image.eveonline.com/' + img_dir + '/' + id + '_' + size + '.' + extension,
				'alt': text,
				'width': size,
				'height': size,
				'class': cls,
			});
			return img;
		},
		'format_isk': function(number) {
			if(number != null) {
				i = parseInt(number = Math.abs(number).toFixed(2)) + '', 
				j = ((j = i.length) > 3) ? j % 3 : 0; 
				return (j ? i.substr(0, j) + ',' : '') + i.substr(j).replace(/(\d{3})(?=\d)/g, "$1" + ',')
			   		+ ('.' + Math.abs(number - i).toFixed(2).slice(2)) + " ISK";
			} else {
				return "(0 ISK)";
			}
		},
		'format_number': function(number) {
			i = parseInt(number = Math.abs(number)) + '', 
			j = ((j = i.length) > 3) ? j % 3 : 0; 
			return (j ? i.substr(0, j) + ',' : '') + i.substr(j).replace(/(\d{3})(?=\d)/g, "$1" + ',');
		},
		'sp_hour': function(primary, secondary) {
			return (primary + secondary/2) * 60;
		},
		'sp_next_level': function(level, multiplier) {
			var levels = [250, 1415, 8000, 45255, 256000];
			return levels[Math.min(level, 4)] * multiplier;
		},
		'to_localtime': function(timestamp) {
			return moment(timestamp).subtract('minutes', new Date().getTimezoneOffset());
		},
		'roman': function(number) {
			// The elusive roman numeral zero
			return [0, 'I', 'II', 'III', 'IV', 'V'][number];
		}, 
		'format_seconds': function(seconds) {
			if (seconds == 0)
				return "None"
			var days = parseInt(seconds / 86400) % 30;
			var hours = parseInt(seconds / 3600) % 24;
			var minutes = parseInt(seconds / 60) % 60;
			var seconds = parseInt(seconds) % 60;
			var day_s = days == 1? " day, " : " days, ";
			var hour_s = hours == 1? " hour, " : " hours, ";
			var minute_s = minutes == 1? " minute, " : " minutes, ";
			var second_s = seconds == 1? " second" : " seconds";
			return ((days > 0)? days+day_s:"") + ((hours > 0)?hours + hour_s: "") + minutes + minute_s + seconds + second_s;
		},
		'time_to_complete': function(sheet, skill, current_level, current_sp) {
			var attr = {164: sheet.charisma + sheet.charismabonus, 
				165: sheet.intelligence + sheet.intelligencebonus,
				166: sheet.memory + sheet.memorybonus,
				167: sheet.perception + sheet.perceptionbonus,
				168: sheet.willpower + sheet.willpowerbonus};
			var attributes = {164:'Charisma', 165:'Intelligence', 166:'Memory', 167:'Perception', 168:'Willpower'};

			var sp_hour = skillbook.sp_hour(attr[skill.primaryattr], attr[skill.secondaryattr]);
			var sp_required = skillbook.sp_next_level(current_level, skill.timeconstant) - current_sp;
			var response = {'seconds': (sp_required/sp_hour) * 3600, 'sp_hour': sp_hour, 'sp_required': sp_required, 
				'primary': attributes[skill.primaryattr], 'secondary': attributes[skill.secondaryattr]};
			return response;
		},
		'estimate_sp': function(start_sp, end_sp, start_time, end_time) {
			var total = end_sp - start_sp;

			// This item is already completed, so we've presumably obtained all of the SP for it
			if(new Date(end_time) < new Date()) {
				return total;
			} else if (new Date(start_time) <= new Date()) {
				var elapsed = (new Date() - new Date(start_time))/1000;
				var total_time = (new Date(end_time) - new Date(start_time))/1000;
				return Math.floor((total/total_time) * elapsed);
			}

			return 0;
		}
	});
})();

