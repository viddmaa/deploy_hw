# Домашнее задание 6

## 1. Скриншот успешной XSS-атаки (до защиты)

![Скриншот9](../Screens/9.png)

## 2. Пример кода функции-санитизера

![Скриншот10](../Screens/10.png)

```python
def clean_comment(text: str) -> str:
    return bleach.clean(
        text,
        tags=["b", "i", "u", "em", "strong"],
        attributes={},
        strip=True
    )
```

## 3. Скриншот заголовков ответа (вкладка Network), где виден CSP

![Скриншот11](../Screens/11.png)

## 4. Скриншот заблокированной атаки (из консоли браузера)

![Скриншот12](../Screens/12.png) 
