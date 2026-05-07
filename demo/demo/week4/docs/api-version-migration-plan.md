# API Version Migration Plan (v1 -> v2)

## Muc tieu

- Trien khai song song `/api/v1/users` va `/api/v2/users`.
- Bao dam backward compatibility trong giai doan chuyen doi.
- Dat muc tieu cat bo v1 vao ngay sunset da cong bo.

## Pham vi thay doi

- Them endpoint moi: `GET /api/v2/users`.
- Duy tri endpoint cu: `GET /api/v1/users` kem deprecation headers.
- Cap nhat OpenAPI de mo ta song song v1/v2.

## Khac biet contract

- `v1`: `users[].name`, `id` la so nguyen.
- `v2`: `users[].full_name`, `id` la chuoi (`usr_*`), them `users[].status` va `meta.count`.

## Ke hoach rollout

1. **Week 1 - Release v2**
   - Deploy backend co ca v1 va v2.
   - Cong bo tai lieu migration cho client.
2. **Week 2-3 - Client migration**
   - Chuyen cac client noi bo sang v2.
   - Theo doi ti le traffic v1/v2 va error rate.
3. **Week 4 - Deprecation notice**
   - Nhac lai deadline sunset cho client con dung v1.
4. **Sunset date**
   - Ngung ho tro v1 theo `Sunset` header da cong bo.

## Monitoring can theo doi

- Ti le request theo version (`v1`, `v2`)
- Error rate theo endpoint (`/api/v1/users`, `/api/v2/users`)
- p95 latency theo endpoint
- Danh sach client van goi v1

## Tieu chi go-live cho sunset

- >=95% request users da sang v2 trong 2 tuan lien tiep.
- Khong con client quan trong nao su dung v1.
- Khong co incident nghiem trong lien quan den v2 trong 14 ngay.
