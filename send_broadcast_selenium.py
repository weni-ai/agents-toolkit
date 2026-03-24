import os
import time
import tempfile

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

HTML_CONTENT = """<!DOCTYPE html>
<html>
<head><title>Weni Webchat Test</title></head>
<body>
<script>
  (function (d, s, u, w, v) {
    if (w[v]) { return; } else { w[v] = !0; }
    let h = d.getElementsByTagName(s)[0], k = d.createElement(s);
    k.onload = function () {
      let l = d.createElement(s); l.src = u; l.async = true;
      h.parentNode.insertBefore(l, k.nextSibling);
    };
    k.async = true; k.src = 'https://cdn.cloud.weni.ai/webchat-latest.umd.js';
    h.parentNode.insertBefore(k, h);
  })(document, 'script',
     'https://weni-staging-integrations.s3.amazonaws.com/apptypes/wwc/08a3d04a-3c2b-4e35-be75-2411f123d99a/script.js',
     window, 'isWeniWebChatAlreadyInserted');
</script>
</body>
</html>"""

MESSAGE = 'envie o broadcast "hello, world!"'
MAX_TABS = 4


def send_message_in_current_tab(driver, html_path):
    driver.get(f"file://{html_path}")
    wait = WebDriverWait(driver, 30)

    launcher = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.weni-launcher"))
    )
    launcher.click()

    textarea = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "textarea.weni-input-box__textarea")
        )
    )

    time.sleep(1)

    textarea.send_keys(MESSAGE)
    time.sleep(0.5)
    textarea.send_keys(Keys.RETURN)

    time.sleep(2)

    textarea = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "textarea.weni-input-box__textarea")
        )
    )
    textarea.send_keys(MESSAGE)
    time.sleep(0.5)
    textarea.send_keys(Keys.RETURN)


def main():
    html_path = os.path.join(tempfile.gettempdir(), "weni_webchat_test.html")
    with open(html_path, "w") as f:
        f.write(HTML_CONTENT)

    chrome_data_dir = tempfile.mkdtemp()
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-file-access-from-files")
    options.add_argument(f"--user-data-dir={chrome_data_dir}")

    driver = webdriver.Chrome(options=options)

    first_tab = None
    tab_count = 0
    try:
        while True:
            if tab_count > 0:
                driver.switch_to.new_window("tab")

            send_message_in_current_tab(driver, html_path)
            tab_count += 1

            if first_tab is None:
                first_tab = driver.current_window_handle

            print(f"[{tab_count}] Message sent (open tabs: {len(driver.window_handles)})")

            while len(driver.window_handles) > MAX_TABS:
                oldest = driver.window_handles[0]
                if oldest == first_tab:
                    oldest = driver.window_handles[1]
                driver.switch_to.window(oldest)
                driver.close()
                print(f"  Closed old tab (now {len(driver.window_handles)})")

            driver.switch_to.window(first_tab)
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"\nBrowser closed or error: {e}")
    finally:
        try:
            driver.quit()
        except Exception:
            pass
        os.remove(html_path)


if __name__ == "__main__":
    main()
