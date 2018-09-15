$(document).ready(function()
{
	if (is_editor)
	{
		$('#show_editor').click(function(e)
		{
			if (list_mode)
				$('.killme').remove();
			$('input[name=ids]').show();
		});

		$('#select_all').click(function(e)
		{
			$('input[name=ids]').each(function(i, o) { if (!o.disabled) o.checked = true; });
			e.preventDefault();
		});

		$('#select_none').click(function(e)
		{
			$('input[name=ids]').each(function(i, o) { if (!o.disabled) o.checked = false; });
			e.preventDefault();
		});

		$('#link_submit_x, #link_submit_h, #link_submit_d, #link_submit_w').click(function(e)
		{
			const delay = $(this).attr('data-delay');
			$('input[name=delay]').val(delay);
			$('#editorform').submit();
			e.preventDefault();
		});
	}

	$('#noop_listmode').click(function(e) { e.preventDefault(); });
	$('#toggle_listmode').click(function(e)
	{
		document.cookie = 'listmode=' + (+(!list_mode)) + ';path=' + cookie_path;
		window.location.reload(true);
		e.preventDefault();
	});

	if (!list_mode)
	{
		$('img.archive_lazy').lazyload();

		$('img.archive_video').hoverIntent(
			function()
			{
				$(this).attr('src', $(this).attr('data-src-animated'));
				$(this).attr('srcset', $(this).attr('data-srcset-animated'));
			},
			function()
			{
				$(this).attr('src', $(this).attr('data-src'));
				$(this).attr('srcset', $(this).attr('data-srcset'));
			});

		$('a.archive_swipebox').swipebox({ useSVG : false, hideBarsOnMobile : false, loopAtEnd: true });
	}
});
