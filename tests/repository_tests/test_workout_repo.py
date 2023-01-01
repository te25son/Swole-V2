from datetime import date

from hypothesis import given
from hypothesis import strategies as st
import pytest
from sqlalchemy.future import Engine
from sqlmodel import Session, select

from swole_v2.database.repositories.workouts import (
    NAME_AND_DATE_MUST_BE_UNIQUE,
    WorkoutRepository,
)
from swole_v2.database.validators import FIELD_CANNOT_BE_EMPTY
from swole_v2.exceptions import BusinessError
from swole_v2.models import User, Workout, WorkoutCreate, WorkoutRead

from ..factories import UserFactory, WorkoutFactory


class TestWorkoutRepository:
    @pytest.fixture(autouse=True)
    def common_fixtures(self, test_database: Engine, test_user: User, test_session: Session) -> None:
        self.database = test_database
        self.session = test_session
        self.user = test_user
        self.repository = WorkoutRepository(self.database)

    def test_workout_get_all(self) -> None:
        user = UserFactory.build()
        workouts = WorkoutFactory.batch(user=user, size=5)
        instances = [user] + workouts

        self.session.add_all(instances)
        self.session.commit()

        for instance in [user] + workouts:
            self.session.refresh(instance)

        result = self.repository.get_all(user.id)

        assert all(isinstance(r, WorkoutRead) for r in result)
        assert len(result) == len(workouts)

    @given(name=st.text(), date=st.dates())
    def test_workout_create(self, name: str, date: date) -> None:
        try:
            create_data = WorkoutCreate(name=name, date=date)

            result = self.repository.create(self.user.id, create_data)

            assert isinstance(result, WorkoutRead)
            assert result.name == name
            assert result.date == date
        except BusinessError as ex:
            assert str(ex) == NAME_AND_DATE_MUST_BE_UNIQUE
        except ValueError as ex:
            assert FIELD_CANNOT_BE_EMPTY.format("name") in str(ex)

    def test_workout_delete_with_valid_id(self) -> None:
        workout = WorkoutFactory.build(user=self.user)

        self.session.add(workout)
        self.session.commit()
        self.session.refresh(workout)
        self.repository.delete(self.user.id, workout.id)  # type: ignore

        assert self.session.exec(select(Workout).where(Workout.id == workout.id)).one_or_none() is None

    def test_workout_delete_with_invalid_id(self) -> None:
        pass
