/* 
* Copyright (c) 2012 Leonardo Cardoso (http://leocardz.com)
* Dual licensed under the MIT (http://www.opensource.org/licenses/mit-license.php)
* and GPL (http://www.opensource.org/licenses/gpl-license.php) licenses.
*
* Version: 0.1.6
* 
*/
(function ($) {
    $.fn.scale = function (options) {
        var settings = $.extend({
            'event': "",
            'action': 'increase',
            'howMany': null,
            'initialSize': this.width(),
            'finalSize': this.width(),
            'pixels': 1,
            'scaleTime': 0,
            'keepScaling': 'no',
            'frequency': 'one',
            'plane': 'both'
        }, options);
        if (settings.event == "" || settings.event == "default") {
			if(settings.howMany == null){
				if(settings.action == 'increase'){
					if(settings.initialSize > settings.finalSize){
						settings.howMany = settings.initialSize - settings.finalSize + 20;
					}
					else{
						settings.howMany = settings.finalSize - settings.initialSize + 20;
					}
				}
				else{
					if(settings.initialSize < settings.finalSize){
						settings.howMany = settings.initialSize - 20;
					}
					else{
						settings.howMany = settings.finalSize - 20;
					}
				}
			}	
            var id = this;
            var blockEvent = false;
            var scaleInterval;
            var sizeCounterUp = 0;
            var resizeTo = settings.initialSize;
            var currentSize = settings.initialSize;
            var finalSize = settings.finalSize;
            var sizeCounterDown = Math.abs(currentSize - finalSize);
            var top = settings.howMany;
            var sizeCounterDownParcial = 0;
            var heightProportion;
            var defaultRestart = false;
            var heightParsed = parseInt($(id).css('height'));
            var widthParsed = parseInt($(id).css('width'));
            if (settings.scaleTime < 0) {
                settings.scaleTime = 0;
            }
            if (settings.pixels <= 0) {
                settings.pixels = 1;
            }
            if (settings.keepScaling == "yes") settings.frequency = "one";
            if (widthParsed > heightParsed) {
                heightProportion = heightParsed / widthParsed;
            } else if (widthParsed < heightParsed) {
                heightProportion = widthParsed / heightParsed;
            } else {
                heightProportion = 1;
            }
            if (blockEvent == false) {
				blockEvent = true;
				scaleInterval = setInterval(function () {
					sizeCounterUp++;
					if (sizeCounterUp < top) {
						if (settings.action == "increase") currentSize += settings.pixels;
						if (settings.action == "decrease") currentSize -= settings.pixels;
						resizeTo = currentSize;
						sizeCounterDownParcial++;
						if (resizeTo < 1) {
							resizeTo = 1;
							sizeCounterUp = top + 1;
						}
					} else if (sizeCounterUp > top && sizeCounterUp < top * 2) {
						if (sizeCounterDownParcial > sizeCounterDown) {
							sizeCounterDownParcial--;
							if (settings.keepScaling == "no") {
								if (settings.action == "increase") currentSize -= settings.pixels;
								if (settings.action == "decrease") currentSize += settings.pixels;
							}
							resizeTo = currentSize;
							if (resizeTo < 1) resizeTo = 1;
						}
					}
					if (sizeCounterUp >= top * 2 - 1) {
						sizeCounterUp = 0;
						clickRestart = true;
						if(stopEvent == true || settings.frequency == "one"){
							blockEvent = false;
							clearInterval(scaleInterval);
							stopEvent = false;
							stopEvent = false;
						}
					}
					if (((resizeTo == settings.initialSize || resizeTo == settings.finalSize) && (settings.frequency == "continuous")) || clickRestart == true) {
						if (clickRestart == true) {
							clickRestart = false;
						}
						sizeCounterUp = 0;
						currentSize = settings.initialSize;
						finalSize = settings.finalSize;
						sizeCounterDown = Math.abs(currentSize - finalSize);
						top = settings.howMany;
						sizeCounterDownParcial = 0;
						sizeCounterUp = 0;
					}
					if (settings.plane == "both") {
						$(id).css({
							width: resizeTo,
							height: resizeTo * heightProportion
						});
					} else if (settings.plane == "horizontal") {
						$(id).css({
							width: resizeTo,
							height: heightParsed
						});
					} else if (settings.plane == "vertical") {
						$(id).css({
							height: resizeTo * heightProportion
						});
					}
				}, settings.scaleTime);
				if (settings.keepScaling == "yes") {
					settings.initialSize += settings.howMany;
				}
			}
            if (settings.keepScaling == "yes") {
                settings.initialSize += settings.howMany;
            }
            blockEvent = true;
        }
        var clickRestart = false;
        if (settings.event == "click") {
			if(settings.howMany == null){
				if(settings.action == 'increase'){
					if(settings.initialSize > settings.finalSize){
						settings.howMany = settings.initialSize - settings.finalSize + 20;
					}
					else{
						settings.howMany = settings.finalSize - settings.initialSize + 20;
					}
				}
				else{
					if(settings.initialSize < settings.finalSize){
						settings.howMany = settings.initialSize - 20;
					}
					else{
						settings.howMany = settings.finalSize - 20;
					}
				}
			}
            var id = this;
            var blockEvent = false;
            var scaleInterval;
            var resizeTo = settings.initialSize;
            var sizeCounterUp = 0;
            var currentSize = settings.initialSize;
            var finalSize = settings.finalSize;
            var sizeCounterDown = Math.abs(currentSize - finalSize);
            var top = settings.howMany;
            var sizeCounterDownParcial = 0;
            var heightProportion;
            var stopEvent = false;
            var heightParsed = parseInt($(id).css('height'));
            var widthParsed = parseInt($(id).css('width'));
            if (settings.scaleTime < 0) {
                settings.scaleTime = 0;
            }
            if (settings.pixels <= 0) {
                settings.pixels = 1;
            }
            if (settings.keepScaling == "yes") settings.frequency = "one";
            if (widthParsed > heightParsed) {
                heightProportion = heightParsed / widthParsed;
            } else if (widthParsed < heightParsed) {
                heightProportion = widthParsed / heightParsed;
            } else {
                heightProportion = 1;
            }
            $(id).click(function () {
               if (blockEvent == false) {
					blockEvent = true;
					scaleInterval = setInterval(function () {
						sizeCounterUp++;
						if (sizeCounterUp < top) {
							if (settings.action == "increase") currentSize += settings.pixels;
							if (settings.action == "decrease") currentSize -= settings.pixels;
							resizeTo = currentSize;
							sizeCounterDownParcial++;
							if (resizeTo < 1) {
								resizeTo = 1;
								sizeCounterUp = top + 1;
							}
						} else if (sizeCounterUp > top && sizeCounterUp < top * 2) {
							if (sizeCounterDownParcial > sizeCounterDown) {
								sizeCounterDownParcial--;
								if (settings.keepScaling == "no") {
									if (settings.action == "increase") currentSize -= settings.pixels;
									if (settings.action == "decrease") currentSize += settings.pixels;
								}
								resizeTo = currentSize;
								if (resizeTo < 1) resizeTo = 1;
							}
						}
						if (sizeCounterUp >= top * 2 - 1) {
							sizeCounterUp = 0;
							clickRestart = true;
							if(stopEvent == true || settings.frequency == "one"){
								blockEvent = false;
								clearInterval(scaleInterval);
								stopEvent = false;
								stopEvent = false;
							}
						}
						if (((resizeTo == settings.initialSize || resizeTo == settings.finalSize) && (settings.frequency == "continuous")) || clickRestart == true) {
							if (clickRestart == true) {
								clickRestart = false;
							}
							sizeCounterUp = 0;
							currentSize = settings.initialSize;
							finalSize = settings.finalSize;
							sizeCounterDown = Math.abs(currentSize - finalSize);
							top = settings.howMany;
							sizeCounterDownParcial = 0;
							sizeCounterUp = 0;
						}
						if (settings.plane == "both") {
							$(id).css({
								width: resizeTo,
								height: resizeTo * heightProportion
							});
						} else if (settings.plane == "horizontal") {
							$(id).css({
								width: resizeTo,
								height: heightParsed
							});
						} else if (settings.plane == "vertical") {
							$(id).css({
								height: resizeTo * heightProportion
							});
						}
					}, settings.scaleTime);
					if (settings.keepScaling == "yes") {
						settings.initialSize += settings.howMany;
					}
				}
				else {
					 stopEvent = true;
                     if (sizeCounterUp >= top * 2 - 1) {
						clearInterval(scaleInterval);
						mouseOverRestart = true;
						sizeCounterUp = 0;
						resizeTo = currentSize = settings.initialSize;
						finalSize = settings.finalSize;
						sizeCounterDown = Math.abs(currentSize - finalSize);
						top = settings.howMany;
						sizeCounterDownParcial = 0;
						blockEvent = false;
					}
                    if (settings.frequency == "one") {
                        if (blockEvent == false) {
                            scaleInterval = setInterval(function () {
                                sizeCounterUp++;
                                if (sizeCounterUp < top) {
                                    if (settings.action == "increase") currentSize += settings.pixels;
                                    if (settings.action == "decrease") currentSize -= settings.pixels;
                                    resizeTo = currentSize;
                                    sizeCounterDownParcial++;
                                    if (resizeTo < 1) {
                                        resizeTo = 1;
                                        sizeCounterUp = top + 1;
                                    }
                                } else if (sizeCounterUp > top && sizeCounterUp < top * 2) {
                                    if (sizeCounterDownParcial > sizeCounterDown) {
                                        sizeCounterDownParcial--;
                                        if (settings.keepScaling == "no") {
                                            if (settings.action == "increase") currentSize -= settings.pixels;
                                            if (settings.action == "decrease") currentSize += settings.pixels;
                                        }
                                        resizeTo = currentSize;
                                        if (resizeTo < 1) resizeTo = 1;
                                    }
                                }
                                if (sizeCounterUp >= top * 2 - 1) {
                                    sizeCounterUp = 0;
									clickRestart = true;
									if(stopEvent == true || settings.frequency == "one"){
										blockEvent = false;
										clearInterval(scaleInterval);
										stopEvent = false;
										stopEvent = false;
									}
                                }
                                if (clickRestart == true) {
                                    if (clickRestart == true) {
                                        clickRestart = false;
                                    }
                                    sizeCounterUp = 0;
                                    currentSize = settings.initialSize;
                                    finalSize = settings.finalSize;
                                    sizeCounterDown = Math.abs(currentSize - finalSize);
                                    top = settings.howMany;
                                    sizeCounterDownParcial = 0;
                                    sizeCounterUp = 0;
                                }
                                if (settings.plane == "both") {
                                    $(id).css({
                                        width: resizeTo,
                                        height: resizeTo * heightProportion
                                    });
                                } else if (settings.plane == "horizontal") {
                                    $(id).css({
                                        width: resizeTo,
                                        height: heightParsed
                                    });
                                } else if (settings.plane == "vertical") {
                                    $(id).css({
                                        height: resizeTo * heightProportion
                                    });
                                }
                            }, settings.scaleTime);
                        }
                        if (settings.keepScaling == "yes") {
                            settings.initialSize += settings.howMany;
                        }
                        blockEvent = true;
                    }
                }
            });
        }
        var mouseOverRestart = false;
        if (settings.event == "mouseover") {
			if(settings.howMany == null){
				if(settings.action == 'increase'){
					if(settings.initialSize > settings.finalSize){
						settings.howMany = settings.initialSize - settings.finalSize + 20;
					}
					else{
						settings.howMany = settings.finalSize - settings.initialSize + 20;
					}
				}
				else{
					if(settings.initialSize < settings.finalSize){
						settings.howMany = settings.initialSize - 20;
					}
					else{
						settings.howMany = settings.finalSize - 20;
					}
				}
			}
            var id = this;
            var blockEvent = false;
            var scaleInterval;
            var resizeTo = settings.initialSize;
            var sizeCounterUp = 0;
            var currentSize = settings.initialSize;
            var finalSize = settings.finalSize;
            var sizeCounterDown = Math.abs(currentSize - finalSize);
            var top = settings.howMany;
            var sizeCounterDownParcial = 0;
            var heightProportion;
            var stopEvent = false;
			var mouseIsOut = false;
            var heightParsed = parseInt($(id).css('height'));
            var widthParsed = parseInt($(id).css('width'));
            if (settings.scaleTime < 0) {
                settings.scaleTime = 0;
            }
            if (settings.pixels <= 0) {
                settings.pixels = 1;
            }
            if (settings.keepScaling == "yes") settings.frequency = "one";
            if (widthParsed > heightParsed) {
                heightProportion = heightParsed / widthParsed;
            } else if (widthParsed < heightParsed) {
                heightProportion = widthParsed / heightParsed;
            } else {
                heightProportion = 1;
            }
            $(id).mouseover(function () {
				mouseIsOut = false;
				if (blockEvent == false) {
					scaleInterval = setInterval(function () {
						sizeCounterUp++;
						if (sizeCounterUp < top) {
							if (settings.action == "increase") currentSize += settings.pixels;
							if (settings.action == "decrease") currentSize -= settings.pixels;
							resizeTo = currentSize;
							sizeCounterDownParcial++;
							if (resizeTo < 1) {
								resizeTo = 1;
								sizeCounterUp = top + 1;
							}
						} else if (sizeCounterUp > top && sizeCounterUp < top * 2) {
							if (sizeCounterDownParcial > sizeCounterDown) {
								sizeCounterDownParcial--;
								if (settings.keepScaling == "no") {
									if (settings.action == "increase") currentSize -= settings.pixels;
									if (settings.action == "decrease") currentSize += settings.pixels;
								}
								resizeTo = currentSize;
								if (resizeTo < 1) resizeTo = 1;
							}
						}
						if (sizeCounterUp >= top * 2 - 1) {
							sizeCounterUp = 0;
							clickRestart = true;
							if(stopEvent == true || settings.frequency == "one"){
								blockEvent = false;
								clearInterval(scaleInterval);
								stopEvent = false;
								stopEvent = false;
							}
						}
						if (((resizeTo == settings.initialSize || resizeTo == settings.finalSize) && (settings.frequency == "continuous")) || mouseOverRestart == true) {
							if(mouseIsOut == false){
								if (mouseOverRestart == true) {
									mouseOverRestart = false;
								}
								sizeCounterUp = 0;
								currentSize = settings.initialSize;
								finalSize = settings.finalSize;
								sizeCounterDown = Math.abs(currentSize - finalSize);
								top = settings.howMany;
								sizeCounterDownParcial = 0;
							}
						}
						if (settings.plane == "both") {
							$(id).css({
								width: resizeTo,
								height: resizeTo * heightProportion
							});
						} else if (settings.plane == "horizontal") {
							$(id).css({
								width: resizeTo,
								height: heightParsed
							});
						} else if (settings.plane == "vertical") {
							$(id).css({
								height: resizeTo * heightProportion
							});
						}
					}, settings.scaleTime);
				}
				if (settings.keepScaling == "yes") {
					settings.initialSize += settings.howMany;
				}
				blockEvent = true;
			});
			$(id).mouseout(function(){
				mouseIsOut = true;
				stopEvent = true;
				if (sizeCounterUp >= top * 2) {
					clearInterval(scaleInterval);
					mouseOverRestart = true;
					sizeCounterUp = 0;
					resizeTo = currentSize = settings.initialSize;
					finalSize = settings.finalSize;
					blockEvent = false;
					sizeCounterDown = Math.abs(currentSize - finalSize);
					top = settings.howMany;
					sizeCounterDownParcial = 0;
				}
				if (settings.frequency == "one") {
                        if (blockEvent == false) {
                            scaleInterval = setInterval(function () {
                                sizeCounterUp++;
                                if (sizeCounterUp < top) {
                                    if (settings.action == "increase") currentSize += settings.pixels;
                                    if (settings.action == "decrease") currentSize -= settings.pixels;
                                    resizeTo = currentSize;
                                    sizeCounterDownParcial++;
                                    if (resizeTo < 1) {
                                        resizeTo = 1;
                                        sizeCounterUp = top + 1;
                                    }
                                } else if (sizeCounterUp > top && sizeCounterUp < top * 2) {
                                    if (sizeCounterDownParcial > sizeCounterDown) {
                                        sizeCounterDownParcial--;
                                        if (settings.keepScaling == "no") {
                                            if (settings.action == "increase") currentSize -= settings.pixels;
                                            if (settings.action == "decrease") currentSize += settings.pixels;
                                        }
                                        resizeTo = currentSize;
                                        if (resizeTo < 1) resizeTo = 1;
                                    }
                                }
                                if (sizeCounterUp >= top * 2 - 1) {
                                    sizeCounterUp = 0;
									clickRestart = true;
									if(stopEvent == true || settings.frequency == "one"){
										blockEvent = false;
										clearInterval(scaleInterval);
										stopEvent = false;
										stopEvent = false;
									}
                                }
                                if (clickRestart == true) {
                                    if (clickRestart == true) {
                                        clickRestart = false;
                                    }
                                    sizeCounterUp = 0;
                                    currentSize = settings.initialSize;
                                    finalSize = settings.finalSize;
                                    sizeCounterDown = Math.abs(currentSize - finalSize);
                                    top = settings.howMany;
                                    sizeCounterDownParcial = 0;
                                    sizeCounterUp = 0;
                                }
                                if (settings.plane == "both") {
                                    $(id).css({
                                        width: resizeTo,
                                        height: resizeTo * heightProportion
                                    });
                                } else if (settings.plane == "horizontal") {
                                    $(id).css({
                                        width: resizeTo,
                                        height: heightParsed
                                    });
                                } else if (settings.plane == "vertical") {
                                    $(id).css({
                                        height: resizeTo * heightProportion
                                    });
                                }
                            }, settings.scaleTime);
                        }
                        if (settings.keepScaling == "yes") {
                            settings.initialSize += settings.howMany;
                        }
                        blockEvent = true;
                    }
			});
		}
    }
})(jQuery);