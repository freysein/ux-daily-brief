from ux_daily_brief.extractors.page import extract_articles


def make_block(title, description, advertising=False):
    label = "<tr><td>ANZEIGE</td></tr>" if advertising else ""

    return f"""
    <table>
      {label}
      <tr>
        <td>
          <table>
            <tr><td><p>{title}</p></td></tr>
            <tr><td><p>{description}</p></td></tr>
            <tr>
              <td>
                <table>
                  <tr>
                    <td>
                      <a href="https://example.com/story">
                        Mehr erfahren
                      </a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
    """


def test_extract_editorial_article():
    html = make_block(
        "Stefan Sagmeister gestaltet Informationsdesign",
        "Eine neue Ausstellung zeigt, wie Daten in visuelle "
        "Geschichten übersetzt werden können."
    )

    result = extract_articles(html)

    assert len(result) == 1
    assert result[0]["source"] == "page"
    assert result[0]["review_status"] == "candidate"


def test_exclude_advertising():
    html = make_block(
        "Ausgezeichnetes Design: Die Kunst des Weglassens",
        "Eine Kamera wird in einer Werbeanzeige vorgestellt.",
        advertising=True,
    )

    assert extract_articles(html) == []


def test_ignore_missing_description():
    html = make_block(
        "Informationsdesign und visuelle Kommunikation",
        ""
    )

    assert extract_articles(html) == []


def test_empty_html():
    assert extract_articles("") == []


def test_page_span_layout_and_ad_exclusion():
    def block(title, description, ad=False):
        label = "<tr><td>ANZEIGE</td></tr>" if ad else ""
        return f"""
        <table>
          {label}
          <tr><td>
            <table>
              <tr><td><span>{title}</span></td></tr>
              <tr><td><span>{description}</span></td></tr>
              <tr><td>
                <table>
                  <tr><td>
                    <a href="https://example.com/{'ad' if ad else 'article'}">
                      Mehr erfahren
                    </a>
                  </td></tr>
                </table>
              </td></tr>
            </table>
          </td></tr>
        </table>
        """

    html = (
        block(
            "Ausgezeichnetes Design als Werbung",
            "Eine umfangreiche bezahlte Produktvorstellung.",
            ad=True,
        )
        + block(
            "Stefan Sagmeister gestaltet Informationsdesign",
            "Eine Ausstellung zeigt, wie komplexe Daten "
            "durch Gestaltung verständlicher werden.",
        )
    )

    articles = extract_articles(html)

    assert len(articles) == 1
    assert articles[0]["title"] == (
        "Stefan Sagmeister gestaltet Informationsdesign"
    )
    assert "komplexe Daten" in articles[0]["excerpt"]


def test_page_span_layout_and_ad_exclusion():
    def block(title, description, ad=False):
        label = "<tr><td>ANZEIGE</td></tr>" if ad else ""
        return f"""
        <table>
          {label}
          <tr><td>
            <table>
              <tr><td><span>{title}</span></td></tr>
              <tr><td><span>{description}</span></td></tr>
              <tr><td>
                <table>
                  <tr><td>
                    <a href="https://example.com/{'ad' if ad else 'article'}">
                      Mehr erfahren
                    </a>
                  </td></tr>
                </table>
              </td></tr>
            </table>
          </td></tr>
        </table>
        """

    html = (
        block(
            "Ausgezeichnetes Design als Werbung",
            "Eine umfangreiche bezahlte Produktvorstellung.",
            ad=True,
        )
        + block(
            "Stefan Sagmeister gestaltet Informationsdesign",
            "Eine Ausstellung zeigt, wie komplexe Daten "
            "durch Gestaltung verständlicher werden.",
        )
    )

    articles = extract_articles(html)

    assert len(articles) == 1
    assert articles[0]["title"] == (
        "Stefan Sagmeister gestaltet Informationsdesign"
    )
    assert "komplexe Daten" in articles[0]["excerpt"]
