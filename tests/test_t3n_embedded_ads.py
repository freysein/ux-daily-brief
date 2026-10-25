from ux_daily_brief.sponsored_content import detect_sponsored_content


def test_embedded_t3n_ads_not_sponsored():
    html = """
    <article>
      <h1>Google Maps with Gemini</h1>
      <div class="c-ad-container">
        <div class="c-ad-label">Anzeige</div>
        <div class="c-ad">
          <div class="c-ad-placeholder">Anzeige</div>
        </div>
      </div>
      <p>Regular editorial content.</p>
    </article>
    """
    assert detect_sponsored_content(html) is False


def test_explicit_sponsored_post_still_blocked():
    html = """
    <article>
      <div class="o-grid -baseline">
        <span class="c-badge">Anzeige</span>
        <span class="u-text-extrasmall">Sponsored Post</span>
      </div>
    </article>
    """
    assert detect_sponsored_content(html) is True


def test_article_label_without_ad_container_blocked():
    html = """
    <article>
      <span class="c-badge">Anzeige</span>
      <p>Paid article content.</p>
    </article>
    """
    assert detect_sponsored_content(html) is True
