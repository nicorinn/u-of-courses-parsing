        function toggleTitle(elementId, toggleButtonTitleShow, toggleButtonTitleHide) {
            var ele = document.getElementById(elementId);
                
            if (ele.title == toggleButtonTitleShow) {
                ele.title = toggleButtonTitleHide;
            }
            else {
                ele.title = toggleButtonTitleShow;
            }
        }    
        
        function toggleClassByID(showHideDiv, class1, class2) {
                var ele = document.getElementById(showHideDiv);
                if(ele.className == class1) {
                    ele.setAttribute("class", class2);
                }
                else {
                    ele.setAttribute("class", class1);
                }
        }   
     
        function ToggleElementByClass(theClass) {
            var allHTMLTags = new Array(); 
            var allHTMLTags=document.getElementsByTagName("*");

            for (i=0; i<allHTMLTags.length; i++) {
                if (allHTMLTags[i].className==theClass) {
                     if(allHTMLTags[i].style.display == "block") {
                        allHTMLTags[i].style.display="none";
                     }
                     else{
                        allHTMLTags[i].style.display="block";
                     }
                }
            }
        }
        
        function ToggleTableOfContent(toggleButtonTitleShow, toggleButtonTitleHide) {
            toggleTitle('TOC_Toggle', toggleButtonTitleShow, toggleButtonTitleHide);
            toggleClassByID('CaptionTOCdiv','Report_TOC','Report_TOCHide');
            ToggleElementByClass('toggleDiv');
            ToggleTableOfContentAriaExpanded('TOC_Toggle');
        }

        function ToggleTableOfContentAriaExpanded(elem) {
            if (document.getElementById(elem).hasAttribute("aria-expanded")) {
                var tog = document.getElementById(elem).getAttribute("aria-expanded") == "true" ? "false" : "true";
                document.getElementById(elem).setAttribute("aria-expanded", tog);
            }
        }

         function RedirectPDFReportURL(url) {

             var qsarr = new Array();
             var qs = window.location.search.substring(1);
             var singleqs = new Array();
             var str = "";
             qsarr = qs.split('&');

             var preview = 0; 
             
             for (i = 0; i < qsarr.length; i++) {
                 singleqs = qsarr[i].split('=');
                 if (singleqs[0].toLowerCase() == 'populate' && singleqs[1] == 1) {
                     preview = 1;
                     break;
                 }                
             } 

             var newUrl = url;  
             if (preview ==1)
                 newUrl = newUrl + '&preview=1';
                 
             window.open(newUrl);
             return false;
         }