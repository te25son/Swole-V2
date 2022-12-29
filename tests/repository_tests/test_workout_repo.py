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

        assert result.success == True
        assert result.product is not None
        assert len(result.product) == len(workouts)
        assert all(workout in result.product for workout in [WorkoutRead(**w.dict()) for w in workouts])

    @given(name=st.text(min_size=1), date=st.dates())
    def test_workout_create(self, name: str, date: date) -> None:
        create_data = WorkoutCreate(name=name, date=date)

        result = self.repository.create(self.user.id, create_data)

        if product := result.product:
            assert result.success == True
            assert len(product) == 1
            assert isinstance(product[0], WorkoutRead)
            assert product[0].name == name
            assert product[0].date == date
        else:
            assert result.success == False
            assert result.message == NAME_AND_DATE_MUST_BE_UNIQUE

    def test_workout_delete_with_valid_id(self) -> None:
        workout = WorkoutFactory.build(user=self.user)

        self.session.add(workout)
        self.session.commit()
        self.session.refresh(workout)

        result = self.repository.delete(self.user.id, workout.id)  # type: ignore

        assert result.success == True
        assert self.session.exec(select(Workout).where(Workout.id == workout.id)).one_or_none() is None

    def test_workout_delete_with_invalid_id(self) -> None:
        pass
