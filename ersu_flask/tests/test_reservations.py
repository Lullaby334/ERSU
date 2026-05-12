from datetime import datetime, timedelta

from app import (
    Equipment,
    EquipmentStatus,
    Notification,
    Reservation,
    ReservationStatus,
    has_conflict,
)



def test_has_conflict_detects_only_active_overlaps(app_ctx, db_session, make_user, make_equipment):
    user = make_user('student1@example.com')
    equipment = make_equipment(serial_number='OSC-100')
    start = datetime.utcnow() + timedelta(days=1)
    end = start + timedelta(hours=2)

    db_session.add(
        Reservation(
            user_id=user.id,
            equipment_id=equipment.id,
            start_at=start,
            end_at=end,
            status=ReservationStatus.APPROVED,
        )
    )
    db_session.commit()

    assert has_conflict(equipment.id, start + timedelta(minutes=30), end + timedelta(minutes=30)) is True
    assert has_conflict(equipment.id, end + timedelta(minutes=1), end + timedelta(hours=1)) is False

    db_session.add(
        Reservation(
            user_id=user.id,
            equipment_id=equipment.id,
            start_at=start + timedelta(days=1),
            end_at=end + timedelta(days=1),
            status=ReservationStatus.CANCELLED,
        )
    )
    db_session.commit()

    assert has_conflict(
        equipment.id,
        start + timedelta(days=1, minutes=15),
        end + timedelta(days=1),
    ) is False



def test_authenticated_user_can_create_reservation(client, login, db_session, make_user, make_equipment):
    user = make_user('student2@example.com', password='sekret123')
    equipment = make_equipment(serial_number='OSC-101')
    login(user.email, 'sekret123')

    start = datetime.utcnow() + timedelta(days=2)
    end = start + timedelta(hours=3)
    response = client.post(
        f'/equipment/{equipment.id}',
        data={
            'start_at': start.isoformat(timespec='minutes'),
            'end_at': end.isoformat(timespec='minutes'),
            'purpose': 'Ćwiczenia laboratoryjne',
        },
        follow_redirects=False,
    )

    reservation = db_session.query(Reservation).filter_by(user_id=user.id, equipment_id=equipment.id).first()
    refreshed_equipment = db_session.get(Equipment, equipment.id)
    notification = db_session.query(Notification).filter_by(user_id=user.id).first()

    assert response.status_code == 302
    assert reservation is not None
    assert reservation.status == ReservationStatus.PENDING
    assert refreshed_equipment.status == EquipmentStatus.RESERVED
    assert notification is not None



def test_reservation_creation_is_blocked_when_time_slot_conflicts(client, login, db_session, make_user, make_equipment):
    user = make_user('student3@example.com', password='sekret123')
    equipment = make_equipment(serial_number='OSC-102')
    start = datetime.utcnow() + timedelta(days=3)
    end = start + timedelta(hours=2)

    db_session.add(
        Reservation(
            user_id=user.id,
            equipment_id=equipment.id,
            start_at=start,
            end_at=end,
            status=ReservationStatus.APPROVED,
        )
    )
    db_session.commit()
    login(user.email, 'sekret123')

    response = client.post(
        f'/equipment/{equipment.id}',
        data={
            'start_at': (start + timedelta(minutes=10)).isoformat(timespec='minutes'),
            'end_at': (end + timedelta(minutes=10)).isoformat(timespec='minutes'),
            'purpose': 'Konflikt testowy',
        },
        follow_redirects=False,
    )

    reservations = db_session.query(Reservation).filter_by(equipment_id=equipment.id).all()

    assert response.status_code == 302
    assert len(reservations) == 1



def test_user_can_cancel_future_reservation(client, login, db_session, make_user, make_equipment):
    user = make_user('student4@example.com', password='sekret123')
    equipment = make_equipment(serial_number='OSC-103', status=EquipmentStatus.RESERVED)
    reservation = Reservation(
        user_id=user.id,
        equipment_id=equipment.id,
        start_at=datetime.utcnow() + timedelta(days=4),
        end_at=datetime.utcnow() + timedelta(days=4, hours=2),
        status=ReservationStatus.PENDING,
    )
    db_session.add(reservation)
    db_session.commit()

    login(user.email, 'sekret123')
    response = client.post(f'/my/reservations/{reservation.id}/cancel', follow_redirects=False)

    refreshed_reservation = db_session.get(Reservation, reservation.id)
    refreshed_equipment = db_session.get(Equipment, equipment.id)

    assert response.status_code == 302
    assert refreshed_reservation.status == ReservationStatus.CANCELLED
    assert refreshed_equipment.status == EquipmentStatus.AVAILABLE
