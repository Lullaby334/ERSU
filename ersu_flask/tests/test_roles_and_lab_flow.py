from datetime import datetime, timedelta

from app import Equipment, EquipmentStatus, Loan, Notification, Reservation, ReservationStatus, Role



def test_student_cannot_access_lab_dashboard(client, login, make_user):
    user = make_user('student5@example.com', password='sekret123', role=Role.STUDENT)
    login(user.email, 'sekret123')

    response = client.get('/lab')

    assert response.status_code == 403



def test_lab_staff_can_approve_checkout_and_checkin_equipment(
    client,
    login,
    db_session,
    make_user,
    make_equipment,
):
    student = make_user('student6@example.com', password='sekret123', role=Role.STUDENT)
    lab_staff = make_user('lab@example.com', password='sekret123', role=Role.LAB_STAFF)
    equipment = make_equipment(serial_number='OSC-104', status=EquipmentStatus.RESERVED)
    reservation = Reservation(
        user_id=student.id,
        equipment_id=equipment.id,
        start_at=datetime.utcnow() + timedelta(days=1),
        end_at=datetime.utcnow() + timedelta(days=1, hours=4),
        status=ReservationStatus.PENDING,
    )
    db_session.add(reservation)
    db_session.commit()

    login(lab_staff.email, 'sekret123')

    approve_response = client.post(f'/lab/reservations/{reservation.id}/approve', follow_redirects=False)
    approved_reservation = db_session.get(Reservation, reservation.id)
    assert approve_response.status_code == 302
    assert approved_reservation.status == ReservationStatus.APPROVED
    assert approved_reservation.approved_by_id == lab_staff.id

    checkout_response = client.post(f'/lab/reservations/{reservation.id}/checkout', follow_redirects=False)
    loan = db_session.query(Loan).filter_by(reservation_id=reservation.id).first()
    refreshed_equipment = db_session.get(Equipment, equipment.id)
    assert checkout_response.status_code == 302
    assert loan is not None
    assert refreshed_equipment.status == EquipmentStatus.LOANED

    checkin_response = client.post(
        f'/lab/loans/{loan.id}/checkin',
        data={
            'condition_note': 'Sprzęt sprawny po zwrocie',
            'equipment_status': EquipmentStatus.AVAILABLE,
        },
        follow_redirects=False,
    )
    refreshed_loan = db_session.get(Loan, loan.id)
    refreshed_equipment = db_session.get(Equipment, equipment.id)
    notifications = db_session.query(Notification).filter_by(user_id=student.id).all()

    assert checkin_response.status_code == 302
    assert refreshed_loan.check_in_at is not None
    assert refreshed_loan.checked_in_by_id == lab_staff.id
    assert refreshed_equipment.status == EquipmentStatus.AVAILABLE
    assert len(notifications) == 3



def test_admin_can_change_user_role(client, login, db_session, make_user):
    admin = make_user('admin@example.com', password='sekret123', role=Role.ADMIN)
    employee = make_user('employee@example.com', password='sekret123', role=Role.EMPLOYEE)
    login(admin.email, 'sekret123')

    response = client.post(
        f'/admin/users/{employee.id}/role',
        data={'role': Role.LAB_STAFF},
        follow_redirects=False,
    )

    refreshed_user = db_session.get(type(employee), employee.id)

    assert response.status_code == 302
    assert refreshed_user.role == Role.LAB_STAFF
