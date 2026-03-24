# from django.utils.deprecation import MiddlewareMixin
# from rest_framework.response import Response

# class APIResponseWrapperMiddleware(MiddlewareMixin):
#     def process_template_response(self, request, response):
#         """
#         Handles TemplateResponse or DRF Response safely.
#         """
#         if isinstance(response, Response):
#             if response.data is not None and not all(
#                 k in response.data for k in ("success", "message", "status", "data")
#             ):
#                 response.data = {
#                     "success": 200 <= response.status_code < 300,
#                     "message": "Request successful" if 200 <= response.status_code < 300 else "Something went wrong",
#                     "status": response.status_code,
#                     "data": response.data,
#                 }
#         return response

#     def process_response(self, request, response):
#         """
#         Fallback for normal HttpResponse (non-DRF).
#         """
#         try:
#             if hasattr(response, "data"):
#                 # DRF Response already handled in process_template_response
#                 return response

#             # Regular HttpResponse
#             if response.get("Content-Type", "").startswith("application/json"):
#                 import json
#                 data = json.loads(response.content.decode("utf-8"))
#                 if not all(k in data for k in ("success", "message", "status", "data")):
#                     wrapped = {
#                         "success": 200 <= response.status_code < 300,
#                         "message": "Request successful" if 200 <= response.status_code < 300 else "Something went wrong",
#                         "status": response.status_code,
#                         "data": data,
#                     }
#                     response.content = json.dumps(wrapped).encode("utf-8")
#             return response
#         except Exception:
#             return response


from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse, HttpResponse
from rest_framework.response import Response
from rest_framework import status as drf_status
import json


class APIResponseWrapperMiddleware(MiddlewareMixin):
    def _wrap_response(self, data, http_status):
        """
        Wrap data into standard response format.
        """
        custom_message = None
        if isinstance(data, dict) and "message" in data:
            custom_message = data.pop("message")

        return {
            "success": 200 <= http_status < 300,
            "message": custom_message
                or ("Request successful" if 200 <= http_status < 300 else "Something went wrong"),
            "status": http_status,
            "data": data or {},
        }

    def process_template_response(self, request, response):
        """
        Wrap DRF Response (TemplateResponse or APIView Response).
        """
        if isinstance(response, Response):
            # Only wrap if not already wrapped
            if response.data is not None and not all(
                k in response.data for k in ("success", "message", "status", "data")
            ):
                response.data = self._wrap_response(response.data, response.status_code)
        return response

    def process_response(self, request, response):
        """
        Wrap HttpResponse (JSON) or other responses.
        """
        try:
            # If it's a DRF Response, it's already handled
            if hasattr(response, "data"):
                return response

            # JSON HttpResponse
            if response.get("Content-Type", "").startswith("application/json"):
                try:
                    data = json.loads(response.content.decode("utf-8"))
                except Exception:
                    data = response.content.decode("utf-8") or {}
                wrapped = self._wrap_response(data if isinstance(data, dict) else {"data": data}, response.status_code)
                return JsonResponse(wrapped, status=response.status_code)

            # If non-JSON HttpResponse (like plain text)
            if isinstance(response, HttpResponse):
                wrapped = self._wrap_response({"data": response.content.decode("utf-8")}, response.status_code)
                return JsonResponse(wrapped, status=response.status_code)

            return response
        except Exception as e:
            # If something fails in middleware, return internal server error wrapped
            wrapped = self._wrap_response({"message": str(e)}, 500)
            return JsonResponse(wrapped, status=500)
