def test_crawl_then_top_words_full_flow(test_client, mock_httpx_success) -> None:
    """
    Testea el flujo completo:
    controller -> service -> repository -> client externo (mockeado).
    """
    crawl_response = test_client.post(
        "/crawl",
        params={"productUrl": "https://www.amazon.com/gp/product/B00VVOCSOU"},
    )

    assert crawl_response.status_code == 200
    crawl_body = crawl_response.json()
    assert crawl_body["status"] == "processed"
    assert crawl_body["new_words"] > 0
    assert "description" in crawl_body

    # Verifica que lo procesado impacta en la lectura del ranking de palabras.
    top_response = test_client.get("/words/top", params={"limit": 5})

    assert top_response.status_code == 200
    top_body = top_response.json()
    assert top_body["limit"] == 5
    assert len(top_body["words"]) > 0


def test_crawl_returns_502_when_external_api_fails(test_client, mock_httpx_error) -> None:
    """
    Testea manejo de error de proveedor externo:
    AmazonClient falla y el controller traduce a HTTP 502.
    """
    response = test_client.post(
        "/crawl",
        params={"productUrl": "https://www.amazon.com/gp/product/B00VVOCSOU"},
    )

    assert response.status_code == 502
    assert "Failed to fetch Amazon page" in response.json()["detail"]


def test_crawl_deduplicates_already_seen_url(test_client, mock_httpx_success) -> None:
    """
    Testea deduplicación end-to-end:
    primera llamada procesa; segunda devuelve already_seen.
    """
    first = test_client.post(
        "/crawl",
        params={"productUrl": "https://www.amazon.com/gp/product/B00VVOCSOU"},
    )
    second = test_client.post(
        "/crawl",
        params={"productUrl": "https://www.amazon.com/gp/product/B00VVOCSOU"},
    )

    assert first.status_code == 200
    assert first.json()["status"] == "processed"

    assert second.status_code == 200
    assert second.json()["status"] == "already_seen"
    assert second.json()["new_words"] == 0
