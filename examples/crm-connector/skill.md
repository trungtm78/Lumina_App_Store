# CRM Connector – Skill Definition

## Mô tả
App này cho phép AI truy cập và quản lý dữ liệu CRM trong cuộc hội thoại.

## Prompt Instructions
Bạn có thể:
- Tra cứu thông tin khách hàng: 'Tìm khách hàng Công ty ABC'
- Tạo deal mới: 'Tạo deal cho khách Nguyễn Văn A, giá trị 50 triệu'
- Cập nhật pipeline: 'Chuyển deal #123 sang giai đoạn Proposal'
- Báo cáo: 'Liệt kê top 10 deal đang mở tuần này'

Khi người dùng hỏi về khách hàng, luôn dùng tool get_crm_contacts trước.
Xác nhận với người dùng trước khi tạo hoặc cập nhật dữ liệu.

## Tools Available
- get_crm_contacts: Tìm kiếm danh sách contacts
- get_crm_deals: Lấy danh sách deals
- create_crm_deal: Tạo deal mới
- update_crm_deal: Cập nhật deal

## References
- Xem refs.md để biết mapping field giữa Lumina và CRM
