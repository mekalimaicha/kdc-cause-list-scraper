"""Old page layout (2072-01-01 .. 2078-09-30), reproduced from the screenshot."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scraper import parse as P

HTML = """<html><body>
<table><tr><th>माननीय न्यायाधीश</th><th>पेशी</th><th>फैसला</th><th>आदेश</th><th>स्थगित</th></tr>
<tr><td>माननीय न्यायाधीश श्री विनोदकुमार पोखरेल</td><td>१</td><td>०</td><td>१</td><td>०</td></tr></table>
<div style="text-align:center">मिति <span style="color:red">२०७८-०९-३०</span> को दैनिक पेशी सूची</div>
<div>माननीय न्यायाधीश श्री विनोदकुमार पोखरेल</div>
<table><tr><th>क्र स</th><th>मुद्दा नं</th><th>दर्ता मिती</th><th>मुद्दा</th><th>पक्ष || विपक्ष</th><th>फाँटवाला</th><th>कैफियत</th></tr>
<tr><td>१</td><td>०७७-CP-५९८०<br>(३९-०७७-१२१५२)</td><td>२०७८-०३-२३</td><td>अंश चलन</td>
<td>नीता पुडासैनी ||&nbsp; मनोज पुडासैनी समेत ३ जना</td><td>पुरानो मुद्दा फाटँ ८<br>(अभियान)</td>
<td>आदेश &gt;&gt; अन्तरकालिन आदेश जारी हुने</td></tr></table>
<div>माननीय न्यायाधीश श्री राजकुमार कोइराला</div>
<table><tr><th>क्र स</th><th>मुद्दा नं</th><th>दर्ता मिती</th><th>मुद्दा</th><th>पक्ष || विपक्ष</th><th>फाँटवाला</th><th>कैफियत</th></tr>
<tr><td>१</td><td>०७७-CP-३९५६<br>(३९-०७७-०७६९८)</td><td>२०७७-११-०६</td><td>करार बमोजिमरकम दिलाई</td>
<td>गुराँस ट्रेडर्स प्रा.लि.&nbsp; ||&nbsp; सौर्य एयरलाइन्स प्रा.लि.</td><td>मुद्दा फाटँ २४<br>(सामान्य)</td>
<td>फैसला / अन्तिम आदेश &gt;&gt;<br>डिसमिस</td></tr></table>
</body></html>"""


def test_old_layout():
    r = P.parse(HTML)
    assert r.heading_date == "2078-09-30"
    assert len(r.judges) == 1 and len(r.causes) == 2
    assert r.causes[0] == ["", "माननीय न्यायाधीश श्री विनोदकुमार पोखरेल", "१", "०७७-CP-५९८०", "(३९-०७७-१२१५२)",
                           "०३/२३/२०७८", "अंश चलन", "नीता पुडासैनी", "मनोज पुडासैनी समेत ३ जना",
                           "पुरानो मुद्दा फाटँ ८ (अभियान)", "", "", "आदेश-अन्तरकालिन आदेश जारी हुने"]
    assert r.causes[1][1] == "माननीय न्यायाधीश श्री राजकुमार कोइराला"
    assert r.causes[1][7:9] == ["गुराँस ट्रेडर्स प्रा.लि.", "सौर्य एयरलाइन्स प्रा.लि."]
    assert r.causes[1][12] == "फैसला / अन्तिम आदेश-डिसमिस"
    assert r.causes[1][10] == "" and r.causes[1][0] == ""
